#!/usr/bin/env python3
"""
面试助手 GUI 界面
使用 PyQt6 实现现代化界面
"""

import sys
import queue
import threading
import time
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QSplitter, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QColor

from config import (
    AUDIO_QUEUE_MAX_SIZE, TENCENT_SECRET_ID, TENCENT_SECRET_KEY, TENCENT_APP_ID,
    TENCENT_ENGINE_MODEL_TYPE, TENCENT_REGION, LLM_PROVIDER,
    QWEN_API_KEY, QWEN_MODEL, QWEN_BASE_URL,
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
)
from audio_device import AudioDeviceManager
from audio_capture import start_capture_thread
from speech_recognizer import start_recognizer_thread
from asr_backend import TencentASR
from llm import LLMProvider, LLMAssistant


class ASRWorker(QThread):
    """语音识别工作线程"""
    
    # 信号：(source, text, timestamp)
    text_recognized = pyqtSignal(str, str, float)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def on_recognition_result(self, source: str, text: str, timestamp: float):
        """识别结果回调（从识别线程调用）"""
        # 发射信号到 GUI 线程
        self.text_recognized.emit(source, text, timestamp)
    
    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()
        self.audio_queue = None
        self.threads = []
        self.recognizer = None
        self.speaker_device = None
        self.microphone_device = None
    
    def run(self):
        """运行 ASR 后台任务"""
        try:
            # 1. 检测设备
            self.status_changed.emit("检测音频设备...")
            self.speaker_device, self.microphone_device = AudioDeviceManager.get_best_devices()
            
            if self.speaker_device is None:
                self.error_occurred.emit("未找到音频捕获设备")
                return
            
            self.status_changed.emit("设备检测完成")
            
            # 2. 初始化 ASR
            self.status_changed.emit("初始化腾讯云 ASR...")
            asr_backend = TencentASR(
                secret_id=TENCENT_SECRET_ID,
                secret_key=TENCENT_SECRET_KEY,
                app_id=TENCENT_APP_ID,
                engine_model_type=TENCENT_ENGINE_MODEL_TYPE,
                region=TENCENT_REGION
            )
            
            # 3. 创建队列
            self.audio_queue = queue.Queue(maxsize=AUDIO_QUEUE_MAX_SIZE)
            
            # 4. 启动识别线程（带回调）
            thread, self.recognizer = start_recognizer_thread(
                self.audio_queue,
                self.stop_event,
                asr_backend,
                on_result_callback=self.on_recognition_result
            )
            self.threads.append(thread)
            
            # 5. 启动捕获线程
            self.status_changed.emit("启动音频捕获...")
            speaker_thread = start_capture_thread(
                self.audio_queue,
                self.speaker_device,
                'speaker',
                self.stop_event
            )
            if speaker_thread:
                self.threads.append(speaker_thread)
            
            if self.microphone_device:
                mic_thread = start_capture_thread(
                    self.audio_queue,
                    self.microphone_device,
                    'microphone',
                    self.stop_event
                )
                if mic_thread:
                    self.threads.append(mic_thread)
            
            self.status_changed.emit("✓ 系统就绪")
            
            # 6. 监听识别结果
            while not self.stop_event.is_set():
                if self.recognizer:
                    # 检查是否有新的识别结果
                    if hasattr(self.recognizer, 'last_speaker_text') and self.recognizer.last_speaker_text:
                        # 通过信号发送给 GUI
                        # 注意：这里我们需要在 SpeechRecognizer 中添加信号机制
                        pass
                
                time.sleep(0.1)
        
        except Exception as e:
            self.error_occurred.emit(f"ASR 初始化失败: {str(e)}")
    
    def stop(self):
        """停止所有线程"""
        self.stop_event.set()
        for thread in self.threads:
            thread.join(timeout=2)


class LLMWorker(QThread):
    """LLM 流式响应工作线程"""
    
    # 信号：(chunk_text, is_done)
    chunk_received = pyqtSignal(str, bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, llm_assistant: LLMAssistant, question: str):
        super().__init__()
        self.llm_assistant = llm_assistant
        self.question = question
    
    def run(self):
        """流式获取 AI 回复"""
        try:
            for chunk in self.llm_assistant.chat_stream(self.question):
                self.chunk_received.emit(chunk, False)
            
            # 完成信号
            self.chunk_received.emit("", True)
        
        except Exception as e:
            self.error_occurred.emit(f"AI 回复失败: {str(e)}")


class InterviewAssistantGUI(QMainWindow):
    """面试助手主界面"""
    
    def __init__(self):
        super().__init__()
        
        # 后端组件
        self.asr_worker = None
        self.llm_assistant = None
        self.llm_worker = None
        
        # 初始化界面
        self.init_ui()
        self.init_llm()
        
        # 定时器：轮询识别结果
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_recognition_results)
        self.poll_timer.start(100)  # 每 100ms 检查一次
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("面试助手 - AI Interview Assistant")
        self.setGeometry(100, 100, 1400, 800)
        
        # 中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题（缩小）
        title = QLabel("🎯 面试助手")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setMaximumHeight(40)  # 限制高度
        main_layout.addWidget(title)
        
        # 分割器：左右两栏（增加拉伸因子，占据更多空间）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, stretch=10)  # 给文本区域更多空间
        
        # 左侧：面试官问题
        left_widget = self.create_left_panel()
        splitter.addWidget(left_widget)
        
        # 右侧：AI 建议
        right_widget = self.create_right_panel()
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([700, 700])
        
        # 控制按钮区域
        control_layout = QHBoxLayout()
        main_layout.addLayout(control_layout)
        
        # 启动按钮（缩小高度）
        self.start_button = QPushButton("🎤 启动语音识别")
        self.start_button.setFont(QFont("Arial", 11))
        self.start_button.setMinimumHeight(40)
        self.start_button.setMaximumHeight(40)
        self.start_button.clicked.connect(self.start_asr)
        control_layout.addWidget(self.start_button)
        
        # 获取 AI 建议按钮（缩小高度）
        self.ask_ai_button = QPushButton("🤖 获取 AI 建议")
        self.ask_ai_button.setFont(QFont("Arial", 11))
        self.ask_ai_button.setMinimumHeight(40)
        self.ask_ai_button.setMaximumHeight(40)
        self.ask_ai_button.setEnabled(False)
        self.ask_ai_button.clicked.connect(self.ask_ai)
        control_layout.addWidget(self.ask_ai_button)
        
        # 清空按钮（缩小高度）
        self.clear_button = QPushButton("🗑️  清空")
        self.clear_button.setFont(QFont("Arial", 11))
        self.clear_button.setMinimumHeight(40)
        self.clear_button.setMaximumHeight(40)
        self.clear_button.clicked.connect(self.clear_all)
        control_layout.addWidget(self.clear_button)
        
        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("准备就绪")
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板：面试官问题"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # 标题（缩小）
        label = QLabel("👔 面试官问题")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        label.setMaximumHeight(30)
        layout.addWidget(label)
        
        # 文本显示区域（增加拉伸因子）
        self.interviewer_text = QTextEdit()
        self.interviewer_text.setReadOnly(True)
        self.interviewer_text.setFont(QFont("Arial", 13))
        self.interviewer_text.setPlaceholderText("等待面试官提问...")
        layout.addWidget(self.interviewer_text, stretch=10)  # 占据大部分空间
        
        # 提示文字（缩小）
        hint = QLabel("💡 提示：面试官说话后会自动显示在这里")
        hint.setFont(QFont("Arial", 9))
        hint.setStyleSheet("color: gray;")
        hint.setMaximumHeight(20)
        layout.addWidget(hint)
        
        return widget
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板：AI 建议"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # 标题（缩小）
        label = QLabel("🤖 AI 回答建议")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        label.setMaximumHeight(30)
        layout.addWidget(label)
        
        # 文本显示区域（增加拉伸因子）
        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        self.ai_text.setFont(QFont("Arial", 13))
        self.ai_text.setPlaceholderText("点击「获取 AI 建议」按钮获取回答建议...")
        layout.addWidget(self.ai_text, stretch=10)  # 占据大部分空间
        
        # 提示文字（缩小）
        hint = QLabel("💡 提示：AI 建议会流式显示，实时更新")
        hint.setFont(QFont("Arial", 9))
        hint.setStyleSheet("color: gray;")
        hint.setMaximumHeight(20)
        layout.addWidget(hint)
        
        return widget
    
    def init_llm(self):
        """初始化 LLM"""
        try:
            if LLM_PROVIDER == "qwen":
                provider = LLMProvider(
                    api_key=QWEN_API_KEY,
                    model=QWEN_MODEL,
                    base_url=QWEN_BASE_URL
                )
            elif LLM_PROVIDER == "openai":
                provider = LLMProvider(
                    api_key=OPENAI_API_KEY,
                    model=OPENAI_MODEL,
                    base_url=OPENAI_BASE_URL or "https://api.openai.com/v1"
                )
            else:
                self.statusBar.showMessage(f"⚠️  未知的 LLM 提供商: {LLM_PROVIDER}")
                return
            
            self.llm_assistant = LLMAssistant(provider)
            self.statusBar.showMessage(f"✓ LLM 已初始化 ({LLM_PROVIDER})")
        
        except Exception as e:
            self.statusBar.showMessage(f"⚠️  LLM 初始化失败: {str(e)}")
    
    def start_asr(self):
        """启动 ASR 后台线程"""
        if self.asr_worker is None:
            self.start_button.setEnabled(False)
            self.start_button.setText("正在启动...")
            
            # 创建并启动 ASR 工作线程
            self.asr_worker = ASRWorker()
            self.asr_worker.status_changed.connect(self.on_asr_status_changed)
            self.asr_worker.error_occurred.connect(self.on_asr_error)
            self.asr_worker.text_recognized.connect(self.on_text_recognized)
            self.asr_worker.start()
        else:
            self.statusBar.showMessage("语音识别已经在运行中")
    
    def on_asr_status_changed(self, status: str):
        """ASR 状态变化"""
        self.statusBar.showMessage(status)
        
        if "就绪" in status:
            self.start_button.setText("✓ 运行中")
            self.start_button.setStyleSheet("background-color: #4CAF50; color: white;")
            self.ask_ai_button.setEnabled(True)
    
    def on_asr_error(self, error: str):
        """ASR 错误"""
        self.statusBar.showMessage(f"❌ {error}")
        self.start_button.setEnabled(True)
        self.start_button.setText("🎤 重新启动")
    
    def poll_recognition_results(self):
        """轮询识别结果（定时器调用）"""
        # 现在使用信号机制，不需要轮询了
        pass
    
    def on_text_recognized(self, source: str, text: str, timestamp: float):
        """接收识别结果（信号槽）"""
        if source == 'speaker':
            self.add_interviewer_question(text)
        else:
            # 麦克风的话也可以显示（可选）
            pass
    
    def get_last_question(self) -> str:
        """获取最后一个问题"""
        text = self.interviewer_text.toPlainText()
        if not text:
            return ""
        
        # 提取最后一个问题（假设格式为 "HH:MM:SS - 问题内容"）
        lines = text.strip().split('\n')
        if lines:
            last_line = lines[-1]
            if ' - ' in last_line:
                return last_line.split(' - ', 1)[1]
        return ""
    
    def add_interviewer_question(self, question: str):
        """添加面试官问题到左侧"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_text = f"\n{timestamp} - {question}\n"
        
        self.interviewer_text.append(formatted_text)
        
        # 滚动到底部
        cursor = self.interviewer_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.interviewer_text.setTextCursor(cursor)
        
        # 高亮最新问题
        self.statusBar.showMessage(f"💬 新问题: {question[:30]}...")
    
    def ask_ai(self):
        """请求 AI 建议"""
        if not self.llm_assistant:
            self.statusBar.showMessage("⚠️  LLM 未初始化")
            return
        
        # 获取最后一个问题
        last_question = self.get_last_question()
        
        if not last_question:
            self.statusBar.showMessage("⚠️  没有检测到面试官问题")
            return
        
        # 清空右侧
        self.ai_text.clear()
        self.ai_text.append("💭 AI 正在思考...\n\n")
        
        # 禁用按钮
        self.ask_ai_button.setEnabled(False)
        self.ask_ai_button.setText("AI 思考中...")
        
        # 启动 LLM 工作线程
        self.llm_worker = LLMWorker(self.llm_assistant, last_question)
        self.llm_worker.chunk_received.connect(self.on_ai_chunk)
        self.llm_worker.error_occurred.connect(self.on_ai_error)
        self.llm_worker.start()
    
    def on_ai_chunk(self, chunk: str, is_done: bool):
        """接收 AI 流式响应"""
        if is_done:
            # 完成
            self.ask_ai_button.setEnabled(True)
            self.ask_ai_button.setText("🤖 获取 AI 建议")
            self.statusBar.showMessage("✓ AI 建议已生成")
        else:
            # 如果是第一个 chunk，清空"思考中"
            current_text = self.ai_text.toPlainText()
            if "思考中" in current_text:
                self.ai_text.clear()
            
            # 追加文本
            cursor = self.ai_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(chunk)
            self.ai_text.setTextCursor(cursor)
            
            # 滚动到底部
            self.ai_text.ensureCursorVisible()
    
    def on_ai_error(self, error: str):
        """AI 错误"""
        self.ai_text.append(f"\n\n❌ {error}")
        self.ask_ai_button.setEnabled(True)
        self.ask_ai_button.setText("🤖 重试")
        self.statusBar.showMessage(f"❌ {error}")
    
    def clear_all(self):
        """清空所有显示"""
        self.interviewer_text.clear()
        self.ai_text.clear()
        self.statusBar.showMessage("已清空")
    
    def closeEvent(self, event):
        """关闭事件：停止所有线程"""
        if self.asr_worker:
            self.asr_worker.stop()
            self.asr_worker.wait()
        
        event.accept()


def main():
    """启动 GUI 应用"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = InterviewAssistantGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

