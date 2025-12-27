# src/llm_client.py

"""
LLM Client Module (Phase 2)
===========================
负责与 LLM API 交互。
遵循 Phase 5 编程规范。
"""

import os
from typing import Dict, Any, List, Optional
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from src.registry import *

class LLMClient:
    """
    LLM 客户端，支持默认配置与自定义配置双模式。
    """

    def __init__(self, mode: str = LLM_MODE_DEFAULT, api_key: str = None, base_url: str = DEFAULT_API_BASE, model: str = DEFAULT_MODEL):
        # 意义: 初始化客户端
        # 作用: 加载 API Key 和 Base URL
        # 关联: 被主程序调用
        
        self.mode = mode
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = None
        
        if mode == LLM_MODE_DEFAULT and not self.api_key:
            # 默认模式：尝试从环境变量读取
            self.api_key = os.environ.get("OPENAI_API_KEY", "DEMO_KEY")
        
        # 初始化 OpenAI 客户端 (如果 Key 有效且库已安装)
        if OpenAI and self.api_key and self.api_key != "DEMO_KEY":
            try:
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception as e:
                print(f"[Warning] Failed to init OpenAI client: {e}")

    def generate_summary(self, text_content: str) -> str:
        """生成总结报告"""
        system_prompt = self.build_system_prompt("请生成一份幽默的年度总结报告，包含：年度群画像、季度小剧场、年度颁奖典礼、社死时刻、年度总结诗。")
        return self.chat_completion(system_prompt, f"以下是部分聊天记录采样：\n{text_content}")

    def analyze_sentiment(self, text_content: str) -> str:
        """生成情感分析"""
        system_prompt = "你是一个情感分析师。请分析以下对话的情感基调，并给出积极/消极/中性评价，以及关键的情绪触发点。请直接返回 HTML 片段。"
        return self.chat_completion(system_prompt, f"以下是部分聊天记录采样：\n{text_content}")

    def chat_completion(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        """
        调用 LLM Chat Completion API。
        """
        # 意义: 发送请求
        # 作用: 封装 OpenAI SDK 调用，处理网络异常
        # 关联: 核心 AI 功能入口
        
        target_model = model if model else self.model
        
        # 1. 尝试真实调用
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"[Error] API Call Failed: {e}. Falling back to Mock.")
        
        # 2. Mock 回退 (用于演示或无 Key 情况)
        return self._mock_response(user_prompt)

    def _mock_response(self, prompt: str) -> str:
        """
        生成模拟数据用于演示。
        """
        print(f"--- [Mock LLM] Mode: {self.mode} ---")
        
        # 简单的关键词匹配以生成稍微相关的 Mock 内容
        if "年度" in prompt or "summary" in prompt.lower():
            return """
            <h3>年度群画像</h3>
            <p><b>🏷️ 标签：赛博精神病院</b></p>
            <p>原因：数据表明，本群夜间活跃度高达 80%，且“哈哈”一词出现频率远超人类正常水平。</p>
            
            <h3>季度小剧场 (Anime Theater)</h3>
            <p><b>Alice (吐槽役):</b> 这一年我们到底聊了些什么？</p>
            <p><b>Bob (复读机):</b> 聊了些什么？+1</p>
            <p><b>Charlie (潜水员):</b> ... (发出抢红包的声音)</p>
            """
        else:
            return f"""
            <h4>季度分析摘要</h4>
            <ul>
            <li><b>核心话题:</b> 摸鱼、游戏、奶茶。</li>
            <li><b>情感倾向:</b> 极度快乐 (Positivity: 0.9)。</li>
            <li><b>高频词:</b> 666, 笑死, 救命。</li>
            </ul>
            <!-- Debug Info: Input length {len(prompt)} -->
            """

    def build_system_prompt(self, stats_injection: str) -> str:
        """
        构建 System Prompt。
        """
        # 意义: Prompt 工程
        # 作用: 注入角色设定和硬性统计数据
        # 关联: Phase 2 Statistical Injection
        
        base_prompt = "你是一个专业的聊天记录分析师，擅长幽默、犀利的点评。请根据提供的对话内容进行分析。请直接返回 HTML 片段，不要包含 Markdown 标记。"
        if stats_injection:
            base_prompt += f"\n\n参考统计数据：\n{stats_injection}"
        return base_prompt
