"""
LLM 对话接口 - 简化版
直接使用 OpenAI SDK，支持所有 OpenAI 兼容接口（包括 Qwen）
"""

from typing import Iterator, Optional


class LLMProvider:
    """通用 LLM 提供商（支持所有 OpenAI 兼容接口）"""
    
    def __init__(self, api_key: str, model: str, base_url: str):
        """
        初始化 LLM 提供商
        
        Args:
            api_key: API Key
            model: 模型名称
            base_url: API 地址
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai 库：pip install openai")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def chat_stream(self, messages: list[dict], system_prompt: Optional[str] = None) -> Iterator[str]:
        """流式对话"""
        # 添加系统提示
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                stream=True,
                temperature=0.7
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            yield f"\n❌ LLM 错误: {e}\n"


class LLMAssistant:
    """
    LLM 助手 - 管理对话历史和上下文
    """
    
    def __init__(self, provider: LLMProvider, system_prompt: Optional[str] = None):
        """
        初始化助手
        
        Args:
            provider: LLM 提供商实例
            system_prompt: 系统提示词
        """
        self.provider = provider
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.conversation_history = []
    
    def _default_system_prompt(self) -> str:
        """默认系统提示词"""
        return """你是一个专业的面试助手。当用户提供面试官的问题时，你需要：

1. 快速理解问题核心
2. 提供简洁、专业的回答建议
3. 突出关键技术点
4. 保持回答在 2-3 分钟的口述长度

回答风格：
- 直接、清晰、有条理
- 先给结论，再解释细节
- 用具体例子支撑观点
- 避免过于冗长的理论

记住：你是在帮助用户准备面试回答，不是在写论文。"""
    
    def add_user_message(self, content: str):
        """添加用户消息到历史"""
        self.conversation_history.append({
            "role": "user",
            "content": content
        })
    
    def add_assistant_message(self, content: str):
        """添加助手消息到历史"""
        self.conversation_history.append({
            "role": "assistant",
            "content": content
        })
    
    def chat_stream(self, question: str) -> Iterator[str]:
        """
        流式对话
        
        Args:
            question: 用户问题（面试官的提问）
        
        Yields:
            AI 回复的文本片段
        """
        # 添加用户消息
        self.add_user_message(f"面试官问题：{question}")
        
        # 流式获取回复
        full_response = ""
        for chunk in self.provider.chat_stream(
            self.conversation_history,
            self.system_prompt
        ):
            full_response += chunk
            yield chunk
        
        # 添加助手回复到历史
        self.add_assistant_message(full_response)
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
    
    def get_history_summary(self) -> str:
        """获取对话历史摘要"""
        if not self.conversation_history:
            return "（无对话历史）"
        
        summary = f"共 {len(self.conversation_history)} 条消息\n"
        for i, msg in enumerate(self.conversation_history[-6:], 1):  # 只显示最近6条
            role = "用户" if msg["role"] == "user" else "AI"
            content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            summary += f"  {i}. [{role}] {content}\n"
        
        return summary

