# src/generator.py

"""
Report Generator Module (Phase 3)
=================================
负责执行 Map-Reduce 流程，调用 LLM 生成报告内容。
遵循 Phase 5 编程规范。
"""

from typing import Dict, List, Any
import json
import time
from src.registry import *
from src.llm_client import LLMClient
from src.prompts import PromptManager

class ReportGenerator:
    """
    报告生成器核心类，协调 LLM Client 和 Prompt Manager。
    """

    def __init__(self, llm_client: LLMClient):
        # 意义: 初始化生成器
        # 作用: 注入 LLM 客户端依赖
        # 关联: 依赖 src.llm_client
        self.llm = llm_client
        self.prompts = PromptManager()

    def generate_quarterly_analysis(self, quarter: str, content: str, model: str = None, is_periodic: bool = False) -> Dict[str, Any]:
        """
        执行 Map 阶段：生成单季度/阶段隐性分析。
        """
        # 意义: Map 任务执行
        # 作用: 调用 LLM 分析单季度数据
        # 关联: 输出 JSON 中间态
        
        prompt = self.prompts.build_map_prompt(quarter, content, is_periodic=is_periodic)
        system_prompt = "你是一个 JSON 生成器。请仅返回合法的 JSON 数据，不要包含 markdown 代码块标记。"
        
        try:
            response = self.llm.chat_completion(system_prompt, prompt, model=model)
            
            # 清理 Markdown 标记
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
                
            return json.loads(clean_response)
            
        except Exception as e:
            print(f"Error in generating quarterly analysis for {quarter}: {e}")
            return {
                "summary": f"{quarter} 分析失败",
                "characters": {},
                "relations": [],
                "vibe": "未知"
            }

    def generate_annual_report(self, quarterly_results: List[Dict], global_stats: Dict, anime_theme: str = "default", custom_theme_prompt: str = "", model: str = None, is_periodic: bool = False) -> Dict[str, Any]:
        """
        执行 Reduce 阶段：生成年度/阶段汇总内容 (JSON)。
        """
        # 意义: Reduce 任务执行
        # 作用: 汇总所有中间态，生成最终文案
        # 关联: 输出 JSON 内容，包含各模块的 HTML 片段
        
        prompt = self.prompts.build_reduce_prompt(quarterly_results, global_stats, anime_theme, custom_theme_prompt, is_periodic=is_periodic)
        system_prompt = "你是一个 JSON 生成器。请仅返回合法的 JSON 数据，不要包含 markdown 代码块标记。"
        
        try:
            response = self.llm.chat_completion(system_prompt, prompt, model=model)
            
            # 清理 Markdown 标记
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
                
            result = json.loads(clean_response)
            
            # Ensure anime_theater exists (fallback for missing key)
            if "anime_theater" not in result or not result["anime_theater"]:
                result["anime_theater"] = "<h3>动漫IP小剧场</h3><p>（AI 似乎忘了生成小剧场，可能是因为 Token 限制或遗漏。请尝试增加 Token 预算或重试。）</p>"
                
            return result
        except Exception as e:
             print(f"Error in generating annual report: {e}")
             return {
                 "portrait": "<h3>群画像</h3><p>生成失败</p>",
                 "quarterly_review": "<h3>深度复盘</h3><p>生成失败</p>",
                 "roasts": "<h3>群成员锐评</h3><p>生成失败</p>",
                 "awards": "<h3>颁奖典礼</h3><p>生成失败</p>",
                 "anime_theater": "<h3>动漫IP小剧场</h3><p>生成失败</p>",
                 "moments": "<h3>社死/搞笑时刻回顾</h3><p>生成失败</p>",
                 "essay": "<h3>总结小作文</h3><p>生成失败</p>"
             }

    def refine_report_html(self, html_content: str, model: str = None) -> str:
        """
        额外功能：对生成的 HTML 报告进行最终修复和 CSS 优化。
        """
        prompt = f"{PROMPT_REFINE_HTML}\n\n{html_content}"
        system_prompt = "你是一个前端专家。请直接返回优化后的 HTML 代码。"
        
        try:
            # 注意：这里可能会消耗较多 Token，取决于 HTML 大小
            response = self.llm.chat_completion(system_prompt, prompt, model=model)
            
            # 清理 Markdown 标记
            clean_response = response.strip()
            if clean_response.startswith("```html"):
                clean_response = clean_response[7:]
            elif clean_response.startswith("```"):
                clean_response = clean_response[3:]
            
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
                
            return clean_response.strip()
        except Exception as e:
            print(f"Error in refining HTML report: {e}")
            return html_content # 如果失败，返回原始内容
