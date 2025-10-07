"""
语音识别 - 消费者线程
职责：从队列取出音频，进行 ASR，输出结果
"""

import queue
import threading
import time

from config import MAX_CONSECUTIVE_ERRORS, SILENCE_THRESHOLD, DEBUG_MODE, SHOW_TIMING
from audio_processor import AudioChunk, AudioProcessor


class SpeechRecognizer:
    """语音识别器 - 消费者线程（使用腾讯云 ASR）"""
    
    def __init__(
        self,
        audio_queue: queue.Queue,
        stop_event: threading.Event,
        asr_backend,
        on_result_callback=None
    ):
        self.audio_queue = audio_queue
        self.stop_event = stop_event
        self.asr_backend = asr_backend
        self.consecutive_errors = 0
        self.on_result_callback = on_result_callback  # GUI 回调函数
        
        # 缓存最新的识别结果
        self.last_speaker_text = ""  # 面试官最后说的话
        self.last_speaker_timestamp = 0  # 时间戳
    
    def run(self):
        """消费者线程主循环"""
        print("消费者线程启动，等待音频数据...")
        
        while not self.stop_event.is_set():
            try:
                # 阻塞等待队列数据
                try:
                    chunk = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # 验证数据类型
                if not isinstance(chunk, AudioChunk):
                    print("⚠️  收到非法数据类型")
                    self.audio_queue.task_done()
                    continue
                
                # 处理音频
                self._process_chunk(chunk)
                self.audio_queue.task_done()
            
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"❌ 消费者线程异常: {e}")
                    import traceback
                    traceback.print_exc()
                break
        
        print("✓ 消费者线程已退出")
    
    def _process_chunk(self, chunk: AudioChunk):
        """
        处理单个音频块
        
        流程：
        1. 验证音频数据
        2. 检查是否为静音
        3. 调用 ASR 模型
        4. 输出结果
        """
        total_start = time.time()
        
        audio_data = chunk.audio_data
        source = chunk.source
        
        # 设置显示标签
        label = "🔊 面试官" if source == 'speaker' else "🎙️  我"
        
        if DEBUG_MODE:
            queue_delay = total_start - chunk.timestamp
            print(f"[{label}] 从队列取出音频，队列延迟: {queue_delay:.3f}秒，音频时长: {chunk.duration:.2f}秒")
        
        # 验证音频数据
        if not AudioProcessor.validate_audio(audio_data):
            print(f"⚠️  [{label}] 音频数据无效")
            return
        
        # 检查静音
        if AudioProcessor.is_silent(audio_data, SILENCE_THRESHOLD):
            if DEBUG_MODE:
                print(f"[{label}] 音频为静音，跳过识别")
            return
        
        # 进行语音识别（使用后端）
        try:
            asr_start = time.time()
            
            # 调用 ASR 后端
            text = self.asr_backend.recognize(audio_data)
            
            asr_elapsed = time.time() - asr_start
            
            # 输出结果
            if text:
                total_elapsed = time.time() - total_start
                
                # 根据来源显示
                if source == 'speaker':
                    print(f"面试官说: {text}")
                    # 缓存面试官的话（用于 AI 回复）
                    self.last_speaker_text = text
                    self.last_speaker_timestamp = time.time()
                    
                    # 调用 GUI 回调（如果有）
                    if self.on_result_callback:
                        try:
                            self.on_result_callback('speaker', text, time.time())
                        except Exception as e:
                            print(f"⚠️  回调函数错误: {e}")
                else:
                    print(f"我说: {text}")
                    
                    # 调用 GUI 回调（如果有）
                    if self.on_result_callback:
                        try:
                            self.on_result_callback('microphone', text, time.time())
                        except Exception as e:
                            print(f"⚠️  回调函数错误: {e}")
                
                # 显示性能统计
                if SHOW_TIMING:
                    print(f"  ⏱️  ASR耗时: {asr_elapsed:.2f}秒 | 总耗时: {total_elapsed:.2f}秒 | 音频时长: {chunk.duration:.2f}秒")
                
                self.consecutive_errors = 0
        
        except Exception as e:
            self.consecutive_errors += 1
            print(f"❌ [{label}] 识别失败 ({self.consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}): {e}")
            
            if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                print(f"❌ 连续失败{MAX_CONSECUTIVE_ERRORS}次，消费者线程退出")
                self.stop_event.set()


def start_recognizer_thread(
    audio_queue: queue.Queue,
    stop_event: threading.Event,
    asr_backend,
    on_result_callback=None
) -> tuple[threading.Thread, SpeechRecognizer]:
    """
    启动语音识别线程的工厂函数
    
    Args:
        audio_queue: 音频队列
        stop_event: 停止事件
        asr_backend: 腾讯云 ASR 实例
        on_result_callback: 识别结果回调函数 (source, text, timestamp)
    
    Returns:
        (thread, recognizer) 线程对象和识别器对象
    """
    recognizer = SpeechRecognizer(audio_queue, stop_event, asr_backend, on_result_callback)
    
    # 启动线程
    thread = threading.Thread(
        target=recognizer.run,
        daemon=False,
        name="Consumer"
    )
    thread.start()
    
    return thread, recognizer

