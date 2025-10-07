"""
音频捕获 - 生产者线程
职责：从音频设备读取数据，检测语音活动，放入队列
"""

import pyaudio
import numpy as np
import time
import queue
import threading
from typing import Literal

from config import (
    FORMAT, RATE, CHUNK_DURATION, MAX_BUFFER_DURATION,
    SILENCE_DURATION, SILENCE_THRESHOLD, DEBUG_MODE
)
from audio_device import DeviceInfo
from audio_processor import AudioProcessor, AudioChunk


class AudioCaptureThread:
    """
    音频捕获线程 - 基于 VAD (Voice Activity Detection) 的智能捕获
    
    工作原理：
    1. 持续读取音频块
    2. 检测到声音 → 开始缓冲
    3. 检测到静音持续 SILENCE_DURATION 秒 → 处理并发送
    4. 缓冲超过 MAX_BUFFER_DURATION 秒 → 强制处理
    """
    
    # 共享 PyAudio 对象（避免 macOS 多线程 bug）
    _shared_pyaudio = None
    _pyaudio_lock = threading.Lock()
    
    def __init__(
        self,
        audio_queue: queue.Queue,
        device_info: DeviceInfo,
        source_type: Literal['speaker', 'microphone'],
        stop_event: threading.Event
    ):
        self.audio_queue = audio_queue
        self.device_info = device_info
        self.source_type = source_type
        self.stop_event = stop_event
        
        # 计算参数
        self.chunk_size = int(device_info.sample_rate * CHUNK_DURATION)
        self.silence_chunks_needed = int(SILENCE_DURATION / CHUNK_DURATION)
        
        # 显示标签
        self.label = "🔊 扬声器" if source_type == 'speaker' else "🎙️  麦克风"
    
    @classmethod
    def _get_shared_pyaudio(cls):
        """获取共享的 PyAudio 对象（线程安全）"""
        with cls._pyaudio_lock:
            if cls._shared_pyaudio is None:
                cls._shared_pyaudio = pyaudio.PyAudio()
            return cls._shared_pyaudio
    
    def run(self):
        """线程主循环"""
        print(f"\n{self.label} 生产者线程启动:")
        print(f"  设备: {self.device_info.name}")
        print(f"  采样率: {self.device_info.sample_rate} Hz")
        print(f"  通道数: {self.device_info.channels}")
        print(f"  静音检测: {SILENCE_DURATION}秒静音后处理")
        
        p = self._get_shared_pyaudio()
        
        try:
            stream = p.open(
                format=FORMAT,
                channels=self.device_info.channels,
                rate=self.device_info.sample_rate,
                input=True,
                input_device_index=self.device_info.index,
                frames_per_buffer=self.chunk_size
            )
            
            # VAD 状态
            audio_buffer = []
            buffer_duration = 0
            silence_chunks_count = 0
            is_speaking = False
            
            while not self.stop_event.is_set():
                try:
                    # 读取音频
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    
                    # 转单声道
                    audio_data = AudioProcessor.to_mono(audio_data, self.device_info.channels)
                    
                    # 归一化
                    audio_float = AudioProcessor.normalize(audio_data)
                    
                    # 静音检测
                    is_silent = AudioProcessor.is_silent(audio_float, SILENCE_THRESHOLD)
                    
                    if not is_silent:
                        # 有声音
                        if not is_speaking:
                            is_speaking = True
                        silence_chunks_count = 0
                        audio_buffer.append(audio_data)
                        buffer_duration += len(audio_data) / self.device_info.sample_rate
                    else:
                        # 静音
                        if is_speaking:
                            silence_chunks_count += 1
                            audio_buffer.append(audio_data)
                            buffer_duration += len(audio_data) / self.device_info.sample_rate
                    
                    # 检查是否需要处理
                    should_process = False
                    if is_speaking and silence_chunks_count >= self.silence_chunks_needed:
                        should_process = True
                    elif is_speaking and buffer_duration >= MAX_BUFFER_DURATION:
                        should_process = True
                    
                    if should_process and len(audio_buffer) > 0:
                        if DEBUG_MODE:
                            print(f"[{self.label}] 检测到完整语音片段，时长: {buffer_duration:.2f}秒，开始处理...")
                        
                        self._process_buffer(audio_buffer, buffer_duration)
                        
                        # 重置状态
                        audio_buffer = []
                        buffer_duration = 0
                        silence_chunks_count = 0
                        is_speaking = False
                
                except Exception as e:
                    if not self.stop_event.is_set():
                        print(f"⚠️  [{self.label}] 读取音频失败: {e}")
                    break
        
        except Exception as e:
            print(f"❌ [{self.label}] 线程异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
            # 不 terminate 共享的 PyAudio 对象（其他线程可能还在使用）
            print(f"✓ [{self.label}] 生产者线程已退出")
    
    def _process_buffer(self, audio_buffer: list, buffer_duration: float):
        """
        处理缓冲的音频数据
        
        流程：
        1. 拼接所有音频块
        2. 重采样到 16kHz
        3. 归一化
        4. 创建 AudioChunk
        5. 放入队列
        """
        process_start = time.time()
        
        # 拼接
        full_audio = np.concatenate(audio_buffer)
        
        # 重采样
        if self.device_info.sample_rate != RATE:
            full_audio = AudioProcessor.resample(
                full_audio,
                self.device_info.sample_rate,
                RATE
            )
        
        # 归一化
        audio_float32 = AudioProcessor.normalize(full_audio)
        
        # 创建 AudioChunk
        chunk = AudioChunk(
            source=self.source_type,
            audio_data=audio_float32,
            timestamp=time.time(),
            duration=buffer_duration
        )
        
        process_elapsed = time.time() - process_start
        
        if DEBUG_MODE:
            print(f"[{self.label}] 音频处理完成，耗时: {process_elapsed:.3f}秒，放入队列...")
        
        # 放入队列（队列满则丢弃最旧的）
        try:
            self.audio_queue.put_nowait(chunk)
            if DEBUG_MODE:
                print(f"[{self.label}] 已放入队列，队列大小: {self.audio_queue.qsize()}")
        except queue.Full:
            if DEBUG_MODE:
                print(f"[{self.label}] 队列已满，丢弃最旧数据")
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.put_nowait(chunk)
            except queue.Empty:
                pass


def start_capture_thread(
    audio_queue: queue.Queue,
    device_info: DeviceInfo,
    source_type: Literal['speaker', 'microphone'],
    stop_event: threading.Event
) -> threading.Thread:
    """
    启动音频捕获线程的工厂函数
    
    Returns:
        已启动的线程对象
    """
    if device_info is None:
        print(f"❌ [{source_type}] 没有可用的捕获设备")
        return None
    
    capture = AudioCaptureThread(audio_queue, device_info, source_type, stop_event)
    
    thread = threading.Thread(
        target=capture.run,
        daemon=False,
        name=f"{source_type.capitalize()}Producer"
    )
    thread.start()
    
    return thread

