#!/usr/bin/env python3
"""
面试辅助工具 - macOS 双通道语音识别
同时捕获扬声器（面试官）和麦克风（你）

重构版本 - 模块化、清晰、易维护
"""

import sys
import signal
import time
import queue
import threading

from config import AUDIO_QUEUE_MAX_SIZE
from config import TENCENT_SECRET_ID, TENCENT_SECRET_KEY, TENCENT_APP_ID
from config import TENCENT_ENGINE_MODEL_TYPE, TENCENT_REGION
from config import LLM_PROVIDER
from config import QWEN_API_KEY, QWEN_MODEL, QWEN_BASE_URL
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from audio_device import AudioDeviceManager
from audio_capture import start_capture_thread
from speech_recognizer import start_recognizer_thread
from keyboard_listener import start_keyboard_listener
from asr_backend import TencentASR
from llm import LLMProvider, LLMAssistant


class InterviewAssistant:
    """面试辅助工具主类 - 协调各个模块"""
    
    def __init__(self):
        self.stop_event = threading.Event()
        self.audio_queue = None
        self.threads = []
        self.speaker_device = None
        self.microphone_device = None
        self.recognizer = None  # 语音识别器（用于获取最新识别结果）
        self.llm_assistant = None  # LLM 助手
    
    def setup_signal_handler(self):
        """注册信号处理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """处理 Ctrl+C 信号"""
        print("\n\n收到退出信号，正在优雅关闭...")
        self.stop_event.set()
    
    def detect_devices(self) -> bool:
        """
        检测音频设备
        
        Returns:
            True if successful, False otherwise
        """
        print("\n[1/3] 检测音频捕获设备...")
        self.speaker_device, self.microphone_device = AudioDeviceManager.get_best_devices()
        
        if self.speaker_device is None:
            print("\n❌ 至少需要扬声器捕获设备才能运行")
            return False
        
        return True
    
    def initialize_recognizer(self) -> bool:
        """
        初始化语音识别器
        
        Returns:
            True if successful, False otherwise
        """
        print("\n[2/3] 初始化语音识别...")
        
        # 创建腾讯云 ASR
        try:
            asr_backend = TencentASR(
                secret_id=TENCENT_SECRET_ID,
                secret_key=TENCENT_SECRET_KEY,
                app_id=TENCENT_APP_ID,
                engine_model_type=TENCENT_ENGINE_MODEL_TYPE,
                region=TENCENT_REGION
            )
        except Exception as e:
            print(f"❌ 腾讯云 ASR 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 创建共享队列
        self.audio_queue = queue.Queue(maxsize=AUDIO_QUEUE_MAX_SIZE)
        
        # 启动识别线程
        thread, recognizer = start_recognizer_thread(
            self.audio_queue,
            self.stop_event,
            asr_backend
        )
        
        if thread is None:
            return False
        
        self.threads.append(thread)
        self.recognizer = recognizer  # 保存识别器引用
        return True
    
    def initialize_llm(self) -> bool:
        """
        初始化 LLM 助手
        
        Returns:
            True if successful, False otherwise
        """
        print("\n初始化 LLM 助手...")
        
        try:
            # 根据配置选择 LLM 提供商
            if LLM_PROVIDER == "qwen":
                if not QWEN_API_KEY:
                    print("⚠️  未配置 Qwen API Key，跳过 LLM 初始化")
                    return False
                
                provider = LLMProvider(
                    api_key=QWEN_API_KEY,
                    model=QWEN_MODEL,
                    base_url=QWEN_BASE_URL
                )
                print(f"  使用 Qwen {QWEN_MODEL}")
                print(f"  API 地址: {QWEN_BASE_URL}")
            
            elif LLM_PROVIDER == "openai":
                if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE" or not OPENAI_API_KEY:
                    print("⚠️  未配置 OpenAI API Key，跳过 LLM 初始化")
                    print("   在 config.py 中设置 OPENAI_API_KEY")
                    return False
                
                provider = LLMProvider(
                    api_key=OPENAI_API_KEY,
                    model=OPENAI_MODEL,
                    base_url=OPENAI_BASE_URL or "https://api.openai.com/v1"
                )
                print(f"  使用 OpenAI {OPENAI_MODEL}")
            
            else:
                print(f"❌ 未知的 LLM 提供商: {LLM_PROVIDER}")
                print(f"   支持的提供商: qwen, openai")
                return False
            
            self.llm_assistant = LLMAssistant(provider)
            print("✓ LLM 助手初始化完成")
            return True
        
        except Exception as e:
            print(f"⚠️  LLM 初始化失败: {e}")
            return False
    
    def start_capture(self):
        """启动音频捕获线程"""
        print("\n[3/3] 启动音频处理线程...")
        
        # 启动扬声器捕获
        speaker_thread = start_capture_thread(
            self.audio_queue,
            self.speaker_device,
            'speaker',
            self.stop_event
        )
        if speaker_thread:
            self.threads.append(speaker_thread)
        
        # 启动麦克风捕获（如果可用）
        if self.microphone_device is not None:
            mic_thread = start_capture_thread(
                self.audio_queue,
                self.microphone_device,
                'microphone',
                self.stop_event
            )
            if mic_thread:
                self.threads.append(mic_thread)
    
    def on_ctrl_v_pressed(self):
        """Ctrl+V 按下时的回调函数 - 发送问题给 AI"""
        if self.recognizer is None or self.llm_assistant is None:
            return
        
        # 获取最新的面试官问题
        question = self.recognizer.last_speaker_text
        
        if not question:
            print("\n⚠️  没有捕获到面试官的问题")
            return
        
        # 显示 AI 回复
        print("\n" + "="*60)
        print(f"📝 面试官问题：{question}")
        print("-"*60)
        print("🤖 AI 建议：")
        
        try:
            # 流式输出 AI 回复
            for chunk in self.llm_assistant.chat_stream(question):
                print(chunk, end='', flush=True)
            print("\n" + "="*60 + "\n")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  AI 回复被中断\n")
        except Exception as e:
            print(f"\n\n❌ AI 回复失败: {e}\n")
    
    def print_status(self):
        """打印系统状态"""
        print("\n" + "="*60)
        print("✓ 系统就绪！")
        print("  🔊 监听扬声器：捕获面试官语音")
        if self.microphone_device:
            print("  🎙️  监听麦克风：捕获你的语音")
        
        if self.llm_assistant:
            print("\n  🤖 AI 助手：已启用")
            print("     按 Ctrl+V 发送问题给 AI")
        
        print("\n提示：开始面试或播放测试音频")
        print("按 Ctrl+C 停止")
        print("="*60 + "\n")
    
    def wait_for_stop(self):
        """等待退出信号"""
        try:
            while not self.stop_event.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n收到键盘中断")
            self.stop_event.set()
    
    def cleanup(self):
        """清理资源，等待线程退出"""
        print("\n等待所有线程退出...")
        
        for thread in self.threads:
            thread.join(timeout=5)
            if thread.is_alive():
                print(f"⚠️  线程 {thread.name} 未能正常退出")
        
        print("✓ 所有线程已退出")
        print("\n程序结束")
    
    def run(self) -> int:
        """
        主运行流程
        
        Returns:
            exit code (0 = success, 1 = error)
        """
        print("="*60)
        print("  面试辅助工具 - 双通道语音识别")
        print("  同时监听：扬声器（面试官）+ 麦克风（你）")
        print("="*60)
        
        # 设置信号处理
        self.setup_signal_handler()
        
        # 1. 检测设备
        if not self.detect_devices():
            return 1
        
        # 2. 初始化识别器
        if not self.initialize_recognizer():
            return 1
        
        # 2.5. 初始化 LLM（可选）
        self.initialize_llm()
        
        # 3. 启动捕获
        self.start_capture()
        
        # 4. 启动键盘监听（如果 LLM 可用）
        if self.llm_assistant:
            keyboard_thread = start_keyboard_listener(
                self.on_ctrl_v_pressed,
                self.stop_event
            )
            if keyboard_thread:
                self.threads.append(keyboard_thread)
        
        # 等待线程启动
        time.sleep(1)
        
        # 4. 打印状态
        self.print_status()
        
        # 5. 等待退出
        self.wait_for_stop()
        
        # 6. 清理
        self.cleanup()
        
        return 0


def main():
    """程序入口"""
    assistant = InterviewAssistant()
    return assistant.run()


if __name__ == "__main__":
    sys.exit(main())

