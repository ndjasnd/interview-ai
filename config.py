"""
音频配置参数
所有魔法数字集中在这里，一目了然
"""

import pyaudio

# ============ 音频基础参数 ============
FORMAT = pyaudio.paInt16
RATE = 16000  # FunASR 要求的采样率
CHUNK_DURATION = 0.1  # 每次读取 100ms
MAX_BUFFER_DURATION = 10  # 最长缓冲 10 秒（支持长问题）
SILENCE_DURATION = 0.8  # 静音持续 0.8 秒后认为问题结束（面试场景）
AUDIO_QUEUE_MAX_SIZE = 20  # 队列大小（支持两个设备）
SILENCE_THRESHOLD = 0.2  # 静音检测阈值（麦克风底噪较高，提高阈值）
INT16_MAX = 32768.0

# ============ 调试开关 ============
DEBUG_MODE = False  # 调试模式（关闭以减少输出）
SHOW_TIMING = True  # 显示性能计时
SHOW_VOLUME = False  # 显示实时音量（已调优，可关闭）

# ============ 错误处理 ============
MAX_CONSECUTIVE_ERRORS = 5  # 最大连续错误次数

# ============ 腾讯云 ASR 配置 ============
# 获取方式：https://console.cloud.tencent.com/cam/capi
TENCENT_SECRET_ID = ""  # 替换为你的 SecretId
TENCENT_SECRET_KEY = ""  # 替换为你的 SecretKey
TENCENT_APP_ID = ""  # 替换为你的 AppId
TENCENT_ENGINE_MODEL_TYPE = "16k_zh"  # 中文模型，16k采样率
TENCENT_REGION = "ap-shanghai"  # 地域：上海

# ============ LLM 配置 ============
LLM_PROVIDER = "qwen"  # "openai", "anthropic", "qwen"

# Qwen（通义千问）配置
QWEN_API_KEY = ""
QWEN_BASE_URL = "http://openai-compatible/v1"
QWEN_MODEL = "qwen-plus"  # qwen-plus, qwen-max, qwen-turbo

# OpenAI 配置
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"  # 替换为你的 OpenAI API Key
OPENAI_MODEL = "gpt-4"  # gpt-4, gpt-3.5-turbo, gpt-4-turbo 等
OPENAI_BASE_URL = None  # 自定义 API 地址（可选，用于第三方兼容接口）

# Anthropic 配置
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"  # 替换为你的 Anthropic API Key
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"  # claude-3-5-sonnet-20241022 等

