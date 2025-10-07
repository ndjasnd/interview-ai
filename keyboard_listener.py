"""
键盘监听 - 捕获快捷键触发 AI 回复
使用 pynput 库监听键盘事件
"""

import threading
import sys
from typing import Callable, Optional


class KeyboardListener:
    """键盘监听器 - 监听 Ctrl+V 快捷键"""
    
    def __init__(
        self,
        on_trigger: Callable,
        stop_event: threading.Event
    ):
        """
        初始化键盘监听器
        
        Args:
            on_trigger: 触发回调函数（按下 Ctrl+V 时调用）
            stop_event: 停止事件
        """
        self.on_trigger = on_trigger
        self.stop_event = stop_event
        self.listener = None
        
        try:
            from pynput import keyboard
            self.keyboard = keyboard
        except ImportError:
            print("⚠️  未安装 pynput 库，键盘监听不可用")
            print("   安装方法：pip install pynput")
            self.keyboard = None
    
    def run(self):
        """启动键盘监听线程"""
        if self.keyboard is None:
            print("❌ 键盘监听不可用（缺少 pynput 库）")
            return
        
        print("\n⌨️  键盘监听已启动")
        print("   按 Ctrl+V 发送面试官问题给 AI")
        print("   按 Ctrl+C 退出程序\n")
        
        # 监听组合键
        with self.keyboard.GlobalHotKeys({
            '<ctrl>+v': self.on_trigger
        }) as self.listener:
            # 等待停止信号
            while not self.stop_event.is_set():
                self.stop_event.wait(0.5)
        
        print("✓ 键盘监听线程已退出")


def start_keyboard_listener(
    on_trigger: Callable,
    stop_event: threading.Event
) -> Optional[threading.Thread]:
    """
    启动键盘监听线程的工厂函数
    
    Args:
        on_trigger: 触发回调函数
        stop_event: 停止事件
    
    Returns:
        线程对象，如果启动失败返回 None
    """
    listener = KeyboardListener(on_trigger, stop_event)
    
    if listener.keyboard is None:
        return None
    
    thread = threading.Thread(
        target=listener.run,
        daemon=False,
        name="KeyboardListener"
    )
    thread.start()
    
    return thread


