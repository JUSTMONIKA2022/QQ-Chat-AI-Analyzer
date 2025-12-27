# src/renderer.py

"""
Report Renderer Module (Phase 4)
================================
负责将分析结果和 AI 生成的内容渲染为最终的 HTML 报告。
遵循 Phase 5 编程规范。
"""

from jinja2 import Environment, FileSystemLoader
import os
import pandas as pd
from typing import Dict, Any
from src.registry import *

class HTMLRenderer:
    """
    HTML 报告渲染器。
    """

    def __init__(self, template_dir: str = "templates"):
        # 意义: 初始化渲染器
        # 作用: 设置 Jinja2 模板环境
        # 关联: 依赖 templates 目录下的 HTML 文件
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template_name = "report.html"

    def render(self, stats: Dict[str, Any], daily_activity: pd.DataFrame, summary: Dict[str, Any], rankings: Dict[str, pd.DataFrame] = None, output_path: str = "output/report.html") -> str:
        """
        渲染并保存报告。
        """
        # 意义: 生成最终文件
        # 作用: 将统计数据 (stats) 和 AI 文案 (ai_content) 注入模板，并保存到磁盘
        # 关联: 被 app.py 调用，输出最终结果
        
        template = self.env.get_template(self.template_name)
        
        # 处理排行榜数据
        processed_rankings = {}
        if rankings:
             for key, df in rankings.items():
                 processed_rankings[key] = df.to_dict('records') if not df.empty else []
        
        # 准备渲染上下文
        context = {
            "title": f"{stats.get('chat_name', '群聊')} - 年度总结报告",
            "stats": stats,
            "daily_activity": daily_activity.to_dict('records') if not daily_activity.empty else [],
            "summary": summary,
            "rankings": processed_rankings,
            "generated_at": pd.Timestamp.now().strftime(DEFAULT_TIME_FORMAT)
        }
        
        html_content = template.render(**context)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return output_path
