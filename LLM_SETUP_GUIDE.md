# LLM AI 助手使用指南

## 功能说明

面试辅助工具现在支持 AI 助手功能：
- 实时捕获面试官的问题
- 按 `Ctrl+V` 将问题发送给 AI
- AI 流式返回专业的回答建议

---

## 快速开始

### 1. 安装依赖

根据你选择的 LLM 提供商安装对应的库：

#### 使用 OpenAI（推荐）

```bash
pip install openai pynput
```

#### 使用 Anthropic Claude

```bash
pip install anthropic pynput
```

---

### 2. 配置 API Key

编辑 `config.py`，设置你的 API Key：

#### OpenAI 配置

```python
# ============ LLM 配置 ============
LLM_PROVIDER = "openai"  # 使用 OpenAI

# OpenAI 配置
OPENAI_API_KEY = "sk-xxx"  # 替换为你的 OpenAI API Key
OPENAI_MODEL = "gpt-4"  # 或 "gpt-3.5-turbo"
OPENAI_BASE_URL = None  # 可选：使用第三方兼容接口
```

**获取 API Key:**
- 官方：https://platform.openai.com/api-keys
- 国内镜像：可搜索"OpenAI 国内镜像"

#### Anthropic Claude 配置

```python
# ============ LLM 配置 ============
LLM_PROVIDER = "anthropic"  # 使用 Claude

# Anthropic 配置
ANTHROPIC_API_KEY = "sk-ant-xxx"  # 替换为你的 Anthropic API Key
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
```

**获取 API Key:** https://console.anthropic.com/

---

### 3. 运行程序

```bash
python main.py
```

你会看到：

```
✓ 系统就绪！
  🔊 监听扬声器：捕获面试官语音
  🎙️  监听麦克风：捕获你的语音

  🤖 AI 助手：已启用
     按 Ctrl+V 发送问题给 AI

⌨️  键盘监听已启动
   按 Ctrl+V 发送面试官问题给 AI
   按 Ctrl+C 退出程序
```

---

## 使用流程

### 1. 面试官提问

程序会自动识别面试官的语音：

```
面试官说: 请介绍一下你在上个项目中遇到的最大技术挑战
  ⏱️  ASR耗时: 0.47秒 | 总耗时: 0.47秒 | 音频时长: 4.40秒
```

### 2. 按 Ctrl+V 获取 AI 建议

按下 `Ctrl+V` 后，AI 会流式返回回答建议：

```
============================================================
📝 面试官问题：请介绍一下你在上个项目中遇到的最大技术挑战
------------------------------------------------------------
🤖 AI 建议：
我会从三个方面回答这个问题：

1. **技术挑战本身**
在上个项目中，我们遇到的最大技术挑战是高并发场景下的数据一致性问题...

2. **解决方案**
我采用了分布式锁 + 事件溯源的架构...

3. **结果和收获**
最终系统性能提升了3倍，学到了...
============================================================
```

### 3. 参考 AI 建议回答

根据 AI 的建议，组织你自己的回答。

---

## 高级配置

### 使用第三方 OpenAI 兼容接口

如果你使用国内镜像或其他兼容 OpenAI API 的服务：

```python
# config.py
OPENAI_BASE_URL = "https://your-mirror-url.com/v1"  # 设置自定义 API 地址
```

### 自定义系统提示词

编辑 `llm.py` 中的 `_default_system_prompt()` 方法：

```python
def _default_system_prompt(self) -> str:
    return """你是一个专业的面试助手...（自定义提示词）"""
```

---

## 故障排查

### 1. "未配置 OpenAI API Key"

确保在 `config.py` 中正确设置了 API Key：

```python
OPENAI_API_KEY = "sk-xxx"  # 不要留空或使用默认值
```

### 2. "未安装 pynput 库"

```bash
pip install pynput
```

### 3. "没有捕获到面试官的问题"

- 确保面试官说话后等待识别完成
- 检查是否正确配置了 BlackHole 音频设备
- 查看终端是否有 "面试官说:" 的输出

### 4. API 调用失败

- 检查网络连接
- 确认 API Key 是否有效
- 查看余额是否充足
- 如果使用第三方接口，确认 `OPENAI_BASE_URL` 配置正确

---

## 费用说明

### OpenAI 费用（参考）

- GPT-4: ~$0.03/1K tokens（输入）+ $0.06/1K tokens（输出）
- GPT-3.5-turbo: ~$0.001/1K tokens（输入）+ $0.002/1K tokens（输出）

一次面试问答大约消耗 500-1000 tokens，费用约：
- GPT-4: $0.05-0.10/次
- GPT-3.5: $0.002-0.004/次

### Anthropic 费用（参考）

- Claude 3.5 Sonnet: ~$0.003/1K tokens（输入）+ $0.015/1K tokens（输出）

---

## 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+V` | 发送面试官问题给 AI |
| `Ctrl+C` | 退出程序 |

---

## 注意事项

1. **隐私保护**
   - 所有对话都会发送到 OpenAI/Anthropic 服务器
   - 不要在面试中泄露公司机密或敏感信息
   - 建议只用于练习和学习

2. **使用建议**
   - AI 的回答仅供参考，需要结合自己的经验
   - 避免照搬 AI 的回答，要用自己的语言表达
   - 面试官可能会追问细节，确保理解 AI 的建议

3. **合规性**
   - 请在合法合规的场景下使用本工具
   - 尊重面试流程和职业道德

---

## 常见问题

### Q: macOS 提示"无法监听键盘"

A: 需要授予终端"辅助功能"权限：
1. 系统偏好设置 → 安全性与隐私 → 隐私 → 辅助功能
2. 添加你的终端应用（如 Terminal.app）

### Q: 可以不使用 AI 功能吗？

A: 可以。如果没有配置 API Key，程序会跳过 LLM 初始化，只保留语音识别功能。

### Q: 可以同时使用两个 LLM 吗？

A: 目前不支持。在 `config.py` 中设置 `LLM_PROVIDER` 为 "openai" 或 "anthropic"。

---

## 开发者信息

LLM 模块支持扩展其他提供商，只需实现 `LLMProvider` 接口：

```python
class CustomProvider(LLMProvider):
    def chat_stream(self, messages: list[dict], system_prompt: Optional[str] = None) -> Iterator[str]:
        # 实现你的逻辑
        yield "response chunk"
```

---

**祝你面试顺利！** 🚀


