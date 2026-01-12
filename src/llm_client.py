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
            # 简单重试机制 (Max 2 times)
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    print(f"[Info] Sending request to {target_model} (Attempt {attempt+1}/{max_retries})...")
                    response = self.client.chat.completions.create(
                        model=target_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        timeout=60  # 设置 60s 超时
                    )
                    content = response.choices[0].message.content
                    if not content:
                        raise ValueError("Empty response from LLM")
                    return content
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"[Error] API Call Failed (Attempt {attempt+1}): {error_msg}")
                    
                    # 如果是最后一次尝试，且是自定义模式，则返回错误 UI
                    if attempt == max_retries - 1:
                        if self.mode != LLM_MODE_DEFAULT:
                            print(f"[Error] All retries failed. Returning error message to UI.")
                            return f"""
                            <div style="border: 2px solid #ff4444; padding: 15px; background: #fff0f0; color: #cc0000; border-radius: 8px; margin: 20px 0; font-family: sans-serif;">
                                <h3 style="margin-top:0; color: #cc0000;">⚠️ AI 生成失败 (API Error)</h3>
                                <div style="margin-bottom: 10px;">
                                    <strong>错误信息:</strong> <code style="background: #eee; padding: 2px 5px; border-radius: 4px;">{error_msg}</code>
                                </div>
                                <ul style="padding-left: 20px; color: #666;">
                                    <li><strong>模型:</strong> {target_model}</li>
                                    <li><strong>地址:</strong> {str(self.client.base_url)}</li>
                                    <li><strong>建议:</strong> 请检查 API Key 余额、网络连通性或模型名称是否正确。</li>
                                </ul>
                            </div>
                            """
                    # 否则继续下一次重试
                    import time
                    time.sleep(1) # Backoff
        
        # 2. Mock 回退 (仅在默认模式或无 Client 时触发)
        if self.mode == LLM_MODE_DEFAULT:
             print("[Info] Using Mock response (Default Mode).")
             return self._mock_response(user_prompt)
        else:
             # Custom 模式下如果没有 Client 初始化成功 (比如一开始 Key 就空的)，也返回错误
             return f"""
             <div style="border: 2px solid #ff9800; padding: 15px; background: #fff8e1; color: #e65100; border-radius: 8px;">
                <h3>⚠️ 客户端未初始化</h3>
                <p>请先在左侧配置并保存有效的 API Key。</p>
             </div>
             """

    def test_connection(self) -> dict:
        """
        测试 API 连接状态 (自检功能)。
        """
        # 意义: 验证配置有效性
        # 作用: 发送极简请求检测连通性，不吞没异常
        # 关联: 前端“测试连接”按钮
        
        if not self.client:
             if self.mode == LLM_MODE_DEFAULT:
                 return {"success": False, "message": "未检测到有效的 API Key。请检查环境变量 OPENAI_API_KEY 是否设置。"}
             else:
                 return {"success": False, "message": "客户端初始化失败。可能是 API Key 为空或 openai 库未安装。"}
        
        # 获取实际使用的 Base URL (OpenAI Client 会自动处理末尾斜杠等)
        actual_url = str(self.client.base_url)
        print(f"[Debug] Testing Connection -> URL: {actual_url}, Key: {self.api_key[:8]}***")

        try:
            # 发送一个极简的测试请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            model_used = response.model
            return {
                "success": True, 
                "message": f"连接成功！\n\n✅ 目标地址: {actual_url}\n✅ 响应模型: {model_used}\n✅ 状态: 通信正常"
            }
        except Exception as e:
            error_msg = str(e)
            print(f"[Debug] Connection Failed: {error_msg}")
            # 尝试提取更友好的错误信息
            if "401" in error_msg:
                return {"success": False, "message": f"认证失败 (401)：请检查您的 API Key 是否正确。\n详细信息: {error_msg}"}
            elif "404" in error_msg:
                return {"success": False, "message": f"请求失败 (404)：可能是 API Base URL 错误或模型名称不正确。\n目标地址: {actual_url}\n详细信息: {error_msg}"}
            elif "429" in error_msg:
                return {"success": False, "message": f"请求过多 (429)：您的账户可能已欠费或达到速率限制。\n详细信息: {error_msg}"}
            else:
                return {"success": False, "message": f"连接测试失败：{error_msg}\n目标地址: {actual_url}"}

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
