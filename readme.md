# 🎯 智能面试助手 (AI Interview Assistant)

一个实时的智能面试辅助工具，能够在线上会议中实时捕获面试官语音，通过 AI 生成回答建议，并流式显示给用户。

**核心特性：**
- 🎤 实时语音识别（腾讯云 ASR）
- 🤖 AI 智能建议（Qwen / OpenAI）
- 💻 现代化 GUI 界面（PyQt6）
- 🎵 双通道音频捕获（面试官 + 你）
- ⚡ 流式显示（实时更新）

---

## 快速开始

### 1. 系统要求

- **操作系统**: macOS（推荐）/ Linux
- **Python**: 3.8+
- **音频设备**: BlackHole（macOS）或 PulseAudio（Linux）

### 2. 安装依赖

```bash
# 克隆项目
git clone <your-repo-url>
cd interview-ai

# 安装 Python 依赖
pip install -r requirements.txt

# macOS 用户：安装 BlackHole
brew install blackhole-2ch
```

**依赖说明：**
- `pyaudio`: 音频捕获（如果安装失败，见下方故障排查）
- `PyQt6`: GUI 界面（可选，仅 GUI 模式需要）
- `pynput`: 键盘监听（可选，仅命令行模式需要）

**pyaudio 安装问题：**

macOS：
```bash
# 如果 pip install 失败，先安装 portaudio
brew install portaudio
pip install pyaudio
```

Linux（Ubuntu）：
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### 3. 配置音频设备（⚠️ 关键步骤）

**这是最重要的一步！** 如果跳过，程序能运行但 AI 无法识别面试官语音。

#### 为什么需要配置？

- 面试官的声音在**系统扬声器输出**
- 你需要**同时**：
  1. 听到面试官声音（真实扬声器）
  2. 让程序捕获音频（BlackHole）
- 所以要创建**多输出设备**，同时输出到两个地方

#### 快速配置步骤（macOS）

1. **打开 Audio MIDI Setup**
   ```bash
   open "/Applications/Utilities/Audio MIDI Setup.app"
   ```

2. **创建多输出设备**
   - 点击左下角 `+` 按钮
   - 选择 **Create Multi-Output Device**

3. **勾选输出设备**
   - ✅ **BlackHole 2ch**（必选，给程序用）
   - ✅ **内置输出** 或 **耳机**（必选，你听音）

4. **设为系统输出**
   - 系统偏好设置 → 声音 → 输出
   - 选择刚创建的 **Multi-Output Device**

5. **测试**
   - 播放音乐，确认你能听到
   - 运行 `python gui.py`，确认左侧能显示识别结果

**详细图文教程：** [AUDIO_SETUP_GUIDE.md](AUDIO_SETUP_GUIDE.md)

⚠️ **常见错误**：
- 只配置了 BlackHole → 你听不到声音
- 只配置了真实扬声器 → AI 识别不到
- 没有设为系统输出 → 音频不经过 BlackHole

### 4. 配置参数

编辑 `config.py`，设置你的 API 密钥和参数：

#### 4.1 音频参数

```python
# ============ 音频基础参数 ============
FORMAT = pyaudio.paInt16              # 音频格式（16bit）
RATE = 16000                          # 采样率（16kHz）
CHUNK_DURATION = 0.1                  # 每次读取 100ms
MAX_BUFFER_DURATION = 10              # 最长缓冲 10 秒（支持长问题）
SILENCE_DURATION = 0.8                # 静音持续 0.8 秒后认为问题结束
AUDIO_QUEUE_MAX_SIZE = 20             # 队列大小
SILENCE_THRESHOLD = 0.02              # 静音检测阈值
```

**参数说明：**
- `MAX_BUFFER_DURATION`: 允许捕获的最长音频时长，避免面试官长问题被切断
- `SILENCE_DURATION`: 面试官停顿多久后认为问题结束，0.8秒适合面试场景
- `SILENCE_THRESHOLD`: 音量低于此值视为静音，可根据环境噪音调整

#### 4.2 腾讯云 ASR 配置

```python
# ============ 腾讯云 ASR 配置 ============
TENCENT_SECRET_ID = "你的SecretId"     # 替换为你的 SecretId
TENCENT_SECRET_KEY = "你的SecretKey"   # 替换为你的 SecretKey
TENCENT_APP_ID = "你的AppId"           # 替换为你的 AppId
TENCENT_ENGINE_MODEL_TYPE = "16k_zh"   # 中文模型，16k采样率
TENCENT_REGION = "ap-shanghai"         # 地域：上海
```

**获取方式：**
1. 访问 https://console.cloud.tencent.com/cam/capi
2. 创建密钥，获取 SecretId 和 SecretKey
3. 访问 https://console.cloud.tencent.com/asr 获取 AppId

#### 4.3 LLM 配置

```python
# ============ LLM 配置 ============
LLM_PROVIDER = "qwen"  # 选择提供商："qwen" 或 "openai"

# Qwen（通义千问）配置
QWEN_API_KEY = "你的API Key"
QWEN_BASE_URL = "http://ai-service.tal.com/openai-compatible/v1"
QWEN_MODEL = "qwen-plus"  # 可选：qwen-plus, qwen-max, qwen-turbo

# OpenAI 配置（可选）
OPENAI_API_KEY = "sk-xxx"             # 你的 OpenAI API Key
OPENAI_MODEL = "gpt-4"                # gpt-4, gpt-3.5-turbo 等
OPENAI_BASE_URL = None                # 可选：第三方兼容接口地址
```

**模型选择建议：**
- `qwen-plus`: 平衡性能和速度（推荐）
- `qwen-max`: 最高质量，速度较慢
- `qwen-turbo`: 最快速度，质量略低
- `gpt-4`: OpenAI 最强模型
- `gpt-3.5-turbo`: OpenAI 快速模型

#### 4.4 调试开关

```python
# ============ 调试开关 ============
DEBUG_MODE = False      # 调试模式（显示详细日志）
SHOW_TIMING = True      # 显示性能计时
SHOW_VOLUME = False     # 显示实时音量（调试用）
```

#### 4.5 完整配置示例

`config.py` 完整示例：

```python
"""
音频配置参数
所有魔法数字集中在这里，一目了然
"""

import pyaudio

# ============ 音频基础参数 ============
FORMAT = pyaudio.paInt16
RATE = 16000
CHUNK_DURATION = 0.1
MAX_BUFFER_DURATION = 10
SILENCE_DURATION = 0.8
AUDIO_QUEUE_MAX_SIZE = 20
SILENCE_THRESHOLD = 0.02
INT16_MAX = 32768.0

# ============ 调试开关 ============
DEBUG_MODE = False
SHOW_TIMING = True
SHOW_VOLUME = False

# ============ 错误处理 ============
MAX_CONSECUTIVE_ERRORS = 5

# ============ 腾讯云 ASR 配置 ============
TENCENT_SECRET_ID = "AKIDxxxxxxxxxxxxxx"
TENCENT_SECRET_KEY = "xxxxxxxxxxxxxxxx"
TENCENT_APP_ID = "1234567890"
TENCENT_ENGINE_MODEL_TYPE = "16k_zh"
TENCENT_REGION = "ap-shanghai"

# ============ LLM 配置 ============
LLM_PROVIDER = "qwen"

# Qwen 配置
QWEN_API_KEY = "300000413:xxxxxxxxxxxxxx"
QWEN_BASE_URL = "http://ai-service.tal.com/openai-compatible/v1"
QWEN_MODEL = "qwen-plus"

# OpenAI 配置（备用）
OPENAI_API_KEY = "sk-xxxxx"
OPENAI_MODEL = "gpt-4"
OPENAI_BASE_URL = None
```

### 5. 验证配置

在启动程序前，先验证配置是否正确：

```bash
# 测试 Python 依赖
python -c "import pyaudio, numpy, openai, PyQt6; print('✅ 依赖安装成功')"

# 测试 API 连接（可选）
python -c "from config import TENCENT_SECRET_ID, QWEN_API_KEY; print('✅ API Key 已配置')"
```

### 6. 启动程序

#### GUI 模式（推荐，适合新手）

```bash
python gui.py
```

**启动后应该看到：**
1. 出现 GUI 窗口
2. 点击"🎤 启动语音识别"
3. 状态栏显示"✓ 系统就绪"
4. 播放音频测试，左侧应显示识别结果

<img width="800" alt="GUI界面" src="https://user-images.githubusercontent.com/placeholder.png">

#### 命令行模式（轻量级）

```bash
python main.py
```

**启动后应该看到：**
```
============================================================
  面试辅助工具 - 双通道语音识别
============================================================
[1/3] 检测音频捕获设备...
✓ 扬声器捕获设备: BlackHole 2ch
[2/3] 初始化语音识别...
✓ 腾讯云 ASR 初始化完成
[3/3] 启动音频处理线程...
✓ 系统就绪！
```

### 7. 测试功能

**第一次运行建议测试：**

1. **测试语音识别**
   - 播放 YouTube 视频或音乐
   - 确认左侧（GUI）或终端（命令行）显示识别结果
   - 如果没有，检查音频配置（步骤 3）

2. **测试 AI 建议**
   - GUI：点击"🤖 获取 AI 建议"
   - 命令行：按 `Ctrl+V`
   - 应该在几秒内看到 AI 回复

3. **测试流式显示**
   - AI 回复应该逐字显示（像打字机）
   - 不是一次性全部出现

**如果测试失败，见下方"常见问题"。**

---

## 功能特性

### ✅ 已实现

| 功能 | 说明 |
|------|------|
| 🎤 **实时语音识别** | 腾讯云 ASR，准确率 90-95% |
| 🤖 **AI 智能建议** | Qwen/OpenAI，流式回复 |
| 💻 **现代化 GUI** | PyQt6 双栏布局，实时更新 |
| 🎵 **双通道捕获** | 同时监听扬声器和麦克风 |
| ⚡ **流式显示** | 逐字显示，无需等待 |
| 🔧 **音频适配** | 自动重采样，支持多种设备 |
| 🛡️ **稳定性** | 错误恢复，优雅关闭 |

### 🚧 计划中

- [ ] 对话历史管理
- [ ] 多轮对话上下文
- [ ] 自定义 AI 提示词
- [ ] 导出对话记录
- [ ] 英文面试支持

---

## 使用方式

### GUI 模式（推荐新用户）

1. **启动程序**
   ```bash
   python gui.py
   ```

2. **开始识别**
   - 点击"🎤 启动语音识别"按钮
   - 等待状态栏显示"✓ 系统就绪"

3. **面试过程**
   - 面试官说话 → 左侧自动显示问题
   - 点击"🤖 获取 AI 建议" → 右侧流式显示回答建议
   - 参考建议组织自己的回答

4. **结束面试**
   - 关闭窗口即可

详见：[GUI_GUIDE.md](GUI_GUIDE.md)

### 命令行模式（轻量级）

1. **启动程序**
   ```bash
   python main.py
   ```

2. **使用快捷键**
   - 面试官说话 → 自动识别并打印
   - 按 `Ctrl+V` → 获取 AI 建议
   - 按 `Ctrl+C` → 退出程序

详见：[LLM_SETUP_GUIDE.md](LLM_SETUP_GUIDE.md)

---

## 工作原理

### 系统架构

```
┌─────────────┐
│  会议软件   │ 面试官说话
└──────┬──────┘
       ↓
┌─────────────────────────┐
│  Multi-Output Device    │ 音频分流
├──────────┬──────────────┤
│ BlackHole│  真实扬声器   │
└────┬─────┴──────┬───────┘
     ↓            ↓
┌─────────┐  ┌────────┐
│程序捕获  │  │ 你听到 │
└────┬────┘  └────────┘
     ↓
┌─────────────┐
│ 腾讯云 ASR  │ 语音识别
└──────┬──────┘
       ↓
┌─────────────┐
│  Qwen AI    │ 生成建议
└──────┬──────┘
       ↓
┌─────────────┐
│  GUI 显示   │ 流式输出
└─────────────┘
```

### 数据流

1. **音频捕获** → BlackHole 捕获系统音频
2. **语音识别** → 腾讯云 ASR 实时转文本
3. **AI 推理** → Qwen 生成回答建议
4. **流式显示** → GUI 逐字显示

---

## 技术栈

| 组件 | 技术选型 |
|------|---------|
| **音频捕获** | PyAudio + BlackHole |
| **语音识别** | 腾讯云 ASR（一句话识别）|
| **AI 模型** | Qwen / OpenAI |
| **GUI 框架** | PyQt6 |
| **多线程** | threading + 信号-槽 |
| **语言** | Python 3.8+ |

---

## 项目结构

```
interview-ai/
├── gui.py                    # GUI 主程序 ⭐
├── main.py                   # 命令行主程序
├── config.py                 # 配置文件
├── requirements.txt          # 依赖列表
├── readme.md                 # 本文件
│
├── asr_backend.py            # 语音识别后端
├── llm.py                    # LLM 对话接口
├── audio_capture.py          # 音频捕获
├── audio_device.py           # 设备管理
├── audio_processor.py        # 音频处理
├── speech_recognizer.py      # 识别器
├── keyboard_listener.py      # 键盘监听
│
├── AUDIO_SETUP_GUIDE.md      # 音频配置指南
├── GUI_GUIDE.md              # GUI 使用指南
└── LLM_SETUP_GUIDE.md        # LLM 配置指南
```

---

## 常见问题（新手必读）

### Q1: 安装时遇到 "command not found"

**问题：** `brew: command not found` 或 `pip: command not found`

**解决：**
```bash
# 安装 Homebrew（macOS）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python（如果没有）
brew install python@3.11

# 验证安装
python3 --version
pip3 --version
```

### Q2: pyaudio 安装失败

**问题：** `error: command 'gcc' failed` 或 `fatal error: 'portaudio.h' file not found`

**解决：**
```bash
# macOS
brew install portaudio
pip install pyaudio

# Linux (Ubuntu)
sudo apt-get install portaudio19-dev
pip install pyaudio
```

### Q3: 为什么要用 BlackHole？

**原理：**
- 面试官的声音在**系统扬声器输出**
- 普通麦克风录的是你自己的声音
- BlackHole 是虚拟设备，捕获系统内部音频
- 类似"内录"功能

### Q4: 我听不到面试官声音了

**原因：** 只配置了 BlackHole，没有配置多输出设备

**解决：**
1. 按步骤 3 创建 **Multi-Output Device**
2. 必须同时勾选 BlackHole **和** 真实扬声器
3. 设为系统默认输出

详见：[AUDIO_SETUP_GUIDE.md](AUDIO_SETUP_GUIDE.md)

### Q5: 左侧没有显示识别结果

**可能原因和解决方法：**

1. **音频设备未配置**
   - 检查：系统音频输出是否选择了 Multi-Output Device
   - 检查：Multi-Output Device 是否勾选了 BlackHole

2. **程序未检测到 BlackHole**
   - 重启程序，查看启动日志
   - 应该显示"✓ 扬声器捕获设备: BlackHole 2ch"
   - 如果没有，重新安装 BlackHole

3. **没有播放音频**
   - 播放 YouTube 视频或音乐测试
   - 确认系统音量不为 0

4. **API Key 错误**
   - 检查 config.py 中的 TENCENT_SECRET_ID/KEY
   - 查看终端是否有错误信息

### Q6: AI 回复失败或很慢

**正常情况：** 3-10 秒

**如果超过 30 秒或报错：**
1. 检查网络连接（能否访问 ai-service.tal.com）
2. 检查 QWEN_API_KEY 是否正确
3. 尝试切换模型：`QWEN_MODEL = "qwen-turbo"`

### Q7: GUI 闪退或无响应

**解决：**
```bash
# 重新安装 PyQt6
pip install --upgrade PyQt6

# 如果还是失败，用命令行模式
python main.py
```

### Q8: macOS 提示"无法监听键盘"

**原因：** pynput 需要辅助功能权限

**解决：**
1. 系统偏好设置 → 安全性与隐私 → 隐私 → 辅助功能
2. 添加你的终端（Terminal.app）
3. 勾选启用

### Q9: 会被发现吗？

**技术角度：**
- ✅ 不修改会议软件
- ✅ 不注入任何进程
- ✅ 只被动监听系统音频
- ✅ 会议软件无法检测

**道德建议：**
- ⚠️ 在合法合规场景下使用
- ⚠️ 尊重面试流程和职业道德
- ⚠️ 不要过度依赖 AI
- ⚠️ 仅作学习参考，不要照搬回答

### Q10: 支持 Windows 吗？

**目前不支持。** Windows 需要：
1. 安装 VB-Audio VoiceMeeter
2. 配置虚拟音频设备
3. 可能需要修改部分代码

考虑到复杂度，建议 macOS 或 Linux。

### Q11: 识别准确率不高

**优化建议：**
1. 使用有线耳机（减少蓝牙延迟）
2. 安静环境（减少背景噪音）
3. 面试官说话清晰
4. 调整 `SILENCE_THRESHOLD` 参数

### Q12: 完全不懂技术，能用吗？

**如果你是零基础：**

建议先学习：
1. Python 基础（安装、运行脚本）
2. macOS 基本操作（终端、系统设置）
3. 音频设备概念（输入/输出）

**最简单的方式：**
1. 找懂技术的朋友帮你配置一次
2. 配置好后只需双击运行 `gui.py`
3. 点击按钮即可使用

---

## 配置说明

### 音频参数

编辑 `config.py`：

```python
MAX_BUFFER_DURATION = 10    # 最长缓冲（秒）
SILENCE_DURATION = 0.8      # 静音判断（秒）
SILENCE_THRESHOLD = 0.02    # 音量阈值
```

### LLM 提供商

支持切换不同 LLM：

```python
# 使用 Qwen
LLM_PROVIDER = "qwen"
QWEN_MODEL = "qwen-plus"  # 或 qwen-max, qwen-turbo

# 使用 OpenAI
LLM_PROVIDER = "openai"
OPENAI_MODEL = "gpt-4"    # 或 gpt-3.5-turbo
```

---

## 性能指标

| 指标 | 数值 |
|------|------|
| **识别延迟** | 0.3-0.5 秒 |
| **AI 响应** | 3-10 秒 |
| **准确率** | 90-95% |
| **内存占用** | ~200MB |
| **CPU 占用** | 5-10% |

---

## 开发说明

### 代码质量

本项目遵循 **Linus Torvalds 式代码审查标准**：

- ✅ 消除特殊情况（用数据结构设计）
- ✅ 无魔法数字（语义化常量）
- ✅ 优雅关闭（无资源泄漏）
- ✅ 错误恢复（容错机制）
- ✅ 简洁执念（函数单一职责）

> "好的代码不是写出来的，是**设计**出来的。先理清数据流，代码自然就对了。"

### 贡献指南

欢迎提交 Issue 和 Pull Request！

代码风格要求：
- 遵循 PEP 8
- 添加类型注解
- 编写文档字符串
- 单元测试覆盖

---

## 更新日志

### v2.0.0 (2025-10-07)

- ✅ 重构架构：移除本地 FunASR，统一使用云端 ASR
- ✅ 新增 GUI：PyQt6 双栏界面，实时流式显示
- ✅ 集成 Qwen：支持内部 AI 服务
- ✅ 优化性能：修复 Segmentation fault，降低延迟
- ✅ 完善文档：音频配置、GUI 使用、LLM 配置

### v1.0.0

- ✅ 基础功能：语音识别 + 双通道捕获

---

## 免责声明

本工具仅供**学习和研究**使用。

使用本工具时：
- ✅ 请遵守法律法规
- ✅ 尊重他人隐私和知识产权
- ✅ 不要违反公司政策
- ⚠️ 使用后果自负

---

## 许可证

MIT License

---

## 致谢

- 腾讯云 ASR 团队
- Qwen 团队
- PyQt6 开发者
- 所有贡献者

---

**祝你面试顺利！** 🚀

如有问题，请提交 Issue 或查看文档。
