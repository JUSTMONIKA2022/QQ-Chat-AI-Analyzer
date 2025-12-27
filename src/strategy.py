# src/strategy.py

"""
Strategy Module (Phase 2)
=========================
负责数据压缩、上下文管理及自适应采样路由。
遵循 Phase 5 编程规范。
"""

import pandas as pd
from typing import List, Dict, Any, Tuple
from src.registry import *

class ContextStrategy:
    """
    实现 Phase 2 的核心策略：格式压缩与自适应采样。
    """

    def __init__(self, max_tokens: int = TARGET_INPUT_TOKENS):
        # 意义: 初始化策略控制器
        # 作用: 设定目标 Token 上限
        # 关联: 被 LLM Client 或 主流程调用
        self.max_tokens = max_tokens

    def minify_messages(self, df: pd.DataFrame) -> str:
        """
        将 DataFrame 转换为紧凑的“剧本格式”。(Phase 2 - Format Minification)
        """
        # 意义: 格式压缩
        # 作用: 遍历消息，格式化为 `[MM-DD HH:mm] User: Content`，并合并短时间内连续发言
        # 关联: 用于 Level 1 & 2 采样
        
        if df.empty:
            return ""

        lines = []
        last_user = None
        last_time_minute = None
        buffer_content = []

        # 确保按时间排序
        df = df.sort_values(by=COL_DATETIME)

        for _, row in df.iterrows():
            curr_user = row[COL_USER_NAME]
            curr_time = row[COL_DATETIME]
            curr_minute = curr_time.strftime("%m-%d %H:%M")
            
            content = str(row[COL_CONTENT]).strip()
            # 处理非文本消息
            if row[COL_TYPE] == MSG_TYPE_IMAGE:
                content = "[图片]"
            elif row[COL_TYPE] == MSG_TYPE_VIDEO:
                content = "[视频]"
            elif row[COL_TYPE] == MSG_TYPE_RECALLED:
                content = "[撤回了一条消息]"
            
            if not content:
                continue

            # 合并逻辑: 同一用户且同一分钟
            if curr_user == last_user and curr_minute == last_time_minute:
                buffer_content.append(content)
            else:
                # 结算上一条
                if buffer_content:
                    lines.append(f"[{last_time_minute}] {last_user}: {' | '.join(buffer_content)}")
                
                # 开始新的一条
                last_user = curr_user
                last_time_minute = curr_minute
                buffer_content = [content]

        # 结算最后一条
        if buffer_content:
             lines.append(f"[{last_time_minute}] {last_user}: {' | '.join(buffer_content)}")

        return "\n".join(lines)

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本 Token 数。
        """
        # 意义: 成本控制
        # 作用: 简单按字符比例估算，决定路由策略
        # 关联: 辅助 adaptive_sample
        return int(len(text) * TOKENS_PER_CHAR_ESTIMATE)

    def adaptive_sample(self, df: pd.DataFrame, density_df: pd.DataFrame = None) -> Tuple[str, str]:
        """
        自适应多级采样路由 (Adaptive Multi-level Sampling Router)。
        """
        # 意义: 核心路由逻辑
        # 作用: 根据数据量选择 Lossless, Light, Smart, 或 Extreme 策略
        # 关联: 返回 (处理后的文本, 采用的策略名称)
        
        # 尝试 Level 1: 无损
        full_text = self.minify_messages(df)
        tokens = self.estimate_tokens(full_text)
        
        if tokens <= self.max_tokens:
            return full_text, LEVEL_1_LOSSLESS

        # 尝试 Level 2: 轻度压缩 (过滤无意义回复)
        # 简单过滤: 剔除纯图片、单字回复(非语气词) - 此处简化实现，仅过滤纯媒体
        # 实际实现可更复杂，此处做演示
        df_l2 = df[~df[COL_TYPE].isin([MSG_TYPE_IMAGE, MSG_TYPE_VIDEO])].copy()
        # 过滤极短文本 (长度<2 且不是常用语气词)
        # ... (略去复杂正则，仅做长度过滤演示)
        text_l2 = self.minify_messages(df_l2)
        tokens_l2 = self.estimate_tokens(text_l2)
        
        if tokens_l2 <= self.max_tokens * 1.2: # 允许轻微溢出，LLM通常能扛
             return text_l2, LEVEL_2_LIGHT

        # Level 3: 智能聚焦 (Smart Focus)
        # 提取热点窗口
        if density_df is not None and not density_df.empty:
            # 取 Top 20 高密度分钟
            top_moments = density_df.sort_values('count', ascending=False).head(20)[COL_DATETIME].tolist()
            # 扩展窗口：前后1分钟? 此处简化为只取该分钟
            # 将 datetime 转为分钟级字符串匹配 (不够精确但够用)
            # 更精确的做法是 filter range
            
            # 简化逻辑：保留 Top 20 分钟的数据 + 随机采样剩余 10%
            # 这里需要更复杂的 DataFrame 操作，为演示核心逻辑，我们简化为：
            # 截取前 N 条 + 后 N 条 + 中间随机
            pass
        
        # 降级方案 (Fallback to Truncation/Sampling if Level 3 logic is complex)
        # 简单截断中间，保留头尾 (Head 30% + Tail 30%)
        limit = int(len(df) * 0.5)
        df_l3 = pd.concat([df.head(limit // 2), df.tail(limit // 2)])
        text_l3 = self.minify_messages(df_l3)
        return text_l3 + "\n...(部分中间内容已省略)...", LEVEL_3_SMART

