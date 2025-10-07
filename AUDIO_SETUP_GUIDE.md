# macOS 音频设置指南

## 问题说明

使用本工具时，你需要**同时**满足两个需求：
1. **自己能听到**面试官的声音（通过真实扬声器）
2. **AI 能识别**面试官的声音（通过 BlackHole 捕获）

如果只选择一个设备，会导致：
- ❌ 只用 BlackHole → AI 能识别，但你听不到
- ❌ 只用真实扬声器 → 你能听到，但 AI 识别不到

**解决方案：创建多输出设备（Multi-Output Device）**

---

## 一次性设置步骤

### 1. 安装 BlackHole

如果还没安装：

```bash
brew install blackhole-2ch
```

或从官网下载：https://existential.audio/blackhole/

---

### 2. 创建多输出设备

#### 打开 Audio MIDI Setup

```bash
open "/Applications/Utilities/Audio MIDI Setup.app"
```

或者：
- Spotlight 搜索 "Audio MIDI Setup"
- 应用程序 → 实用工具 → Audio MIDI Setup

#### 创建多输出设备

1. 点击左下角 **+** 按钮
2. 选择 **Create Multi-Output Device**（创建多输出设备）

<img width="400" alt="创建多输出设备" src="https://user-images.githubusercontent.com/placeholder.png">

#### 配置输出目标

在右侧面板中，勾选以下设备：

- ✅ **BlackHole 2ch**（必选，用于程序捕获）
- ✅ **内置输出** 或 **External Headphones**（用于你听到声音）

⚠️ **注意顺序**：
- 将 **内置输出** 或 **External Headphones** 放在**第一位**（主输出）
- BlackHole 2ch 放在第二位

可以通过拖拽调整顺序。

#### 重命名（可选）

右键新设备 → **Rename**，改名为：
- `Interview Audio Output`
- 或任何你喜欢的名字

---

### 3. 设置为系统输出

#### 方法 1：在 Audio MIDI Setup 中设置

右键新创建的 Multi-Output Device → **Use This Device For Sound Output**

#### 方法 2：在系统设置中选择

1. 系统偏好设置 → 声音 → 输出
2. 选择 **Multi-Output Device**（或你重命名的设备）

---

### 4. 测试设置

#### 测试音频输出

播放任意音频（如 YouTube 视频）：
- ✅ 你应该能通过扬声器/耳机听到声音
- ✅ 运行 `python main.py`，AI 应该能识别到声音

#### 验证音频路由

```bash
# 播放测试音频
say "这是一个测试" &

# 运行程序
python main.py
```

你应该：
1. 听到 "这是一个测试"（从真实扬声器）
2. 看到终端输出识别结果（AI 捕获到了）

---

## 使用 AirPods 的特殊说明

如果你使用 AirPods（或其他蓝牙耳机）：

### 选项 1：创建包含 AirPods 的多输出设备

在 Multi-Output Device 中勾选：
- ✅ **BlackHole 2ch**
- ✅ **AirPods**（或你的蓝牙设备名称）

⚠️ **限制**：多输出设备不支持音量控制，所有输出音量相同。

### 选项 2：使用 Aggregate Device（推荐）

如果需要独立控制音量：

1. 在 Audio MIDI Setup 中创建 **Aggregate Device**
2. 勾选 BlackHole 2ch 和 AirPods
3. 在应用程序中选择这个 Aggregate Device

---

## 常见问题

### Q1: 我听不到声音了

**检查项：**
1. 确认多输出设备中勾选了真实扬声器
2. 确认真实扬声器在勾选列表的**第一位**
3. 系统音量没有静音

**解决方法：**
- 在 Audio MIDI Setup 中调整设备顺序
- 或者临时切换回单一输出设备

---

### Q2: AI 识别不到声音

**检查项：**
1. 确认多输出设备中勾选了 **BlackHole 2ch**
2. 运行 `python main.py`，查看是否检测到 BlackHole 设备
3. 确认会议软件的音频输出设置正确

**解决方法：**
```bash
# 查看程序是否检测到 BlackHole
python main.py

# 应该看到：
# ✓ 扬声器捕获设备: BlackHole 2ch (索引 0)
```

---

### Q3: 会议软件中对方听不到我的声音

这与本设置**无关**。多输出设备只影响**输出**（你听到什么），不影响**输入**（你的麦克风）。

检查会议软件的麦克风设置：
- Zoom/Teams/Meet → 设置 → 音频
- 输入设备：选择你的真实麦克风（不要选 BlackHole）

---

### Q4: 设置后音质变差或有延迟

**原因：** 多输出设备可能导致轻微延迟或音质下降。

**解决方法：**
1. 在 Audio MIDI Setup 中点击多输出设备
2. 右侧面板调整 **Sample Rate**（采样率）：
   - 设置为 **48000 Hz**（推荐）
3. 确保所有输出设备的采样率一致

---

### Q5: 面试结束后如何恢复

**临时切换（推荐）：**
- 系统偏好设置 → 声音 → 输出
- 切换回 **内置输出** 或 **AirPods**

**永久删除：**
- 在 Audio MIDI Setup 中右键 Multi-Output Device
- 选择 **Remove Device**

---

## 快速诊断脚本

运行此脚本检查音频设置：

```bash
python -c "
import pyaudio
p = pyaudio.PyAudio()
print('=== 可用输出设备 ===')
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxOutputChannels'] > 0:
        print(f'{i}: {info[\"name\"]}')
p.terminate()
"
```

---

## 推荐设置总结

### 面试时（使用 AI 助手）

- 输出：**Multi-Output Device**（BlackHole + 扬声器）
- 输入：**真实麦克风**（不要选 BlackHole）

### 平时使用

- 输出：**内置输出** 或 **AirPods**
- 输入：**真实麦克风**

---

## 视觉示意图

```
                    面试官声音（来自会议软件）
                              ↓
                    系统音频输出（Multi-Output）
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
            真实扬声器            BlackHole 2ch
                ↓                       ↓
            你的耳朵              程序捕获 → ASR
                                        ↓
                                    腾讯云识别
                                        ↓
                                    AI 建议
```

---

## 故障排除清单

使用本清单逐项检查：

- [ ] BlackHole 已安装
- [ ] 创建了 Multi-Output Device
- [ ] Multi-Output Device 中勾选了 BlackHole 2ch
- [ ] Multi-Output Device 中勾选了真实扬声器
- [ ] 系统输出设备选择了 Multi-Output Device
- [ ] 运行 `python main.py` 可以看到 BlackHole 设备
- [ ] 播放测试音频时能听到声音
- [ ] 播放测试音频时 AI 能识别

全部勾选 → ✅ 设置完成！

---

**祝你面试顺利！** 🚀

