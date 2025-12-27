# src/analyzer.py

"""
Chat Analyzer Module
====================
负责对 DataFrame 进行统计分析。
遵循 Phase 5 编程规范。
"""

import pandas as pd
import jieba
from collections import Counter
from typing import Dict, List, Tuple, Any
from src.registry import *

class ChatAnalyzer:
    """
    提供多种维度的聊天记录统计分析功能。
    """
    
    def __init__(self, df: pd.DataFrame):
        # 意义: 初始化分析器
        # 作用: 接收 DataFrame 并进行预处理（如过滤无效数据）
        # 关联: 被主程序调用，依赖 src.parser 的输出
        self.df = df
        self.msg_df = self.df.copy() # 目前不做复杂过滤，保留全量用于某些统计

    def get_basic_stats(self) -> Dict[str, Any]:
        """
        获取聊天记录的基础统计信息。
        """
        # 意义: 生成概览数据
        # 作用: 计算总消息数、用户数、图片数、撤回数等
        # 关联: 用于报告首页展示
        
        if self.df.empty:
            return {}
            
        return {
            "total_messages": len(self.df),
            "total_users": self.df[COL_USER_ID].nunique(),
            "total_images": self.df[COL_IMAGE_COUNT].sum(),
            "total_recalled": self.df[COL_IS_RECALLED].sum(),
            "days_covered": (self.df[COL_DATETIME].max() - self.df[COL_DATETIME].min()).days if not self.df.empty else 0
        }

    def get_hardcore_stats(self, top_n: int = 5) -> Dict[str, Any]:
        """
        获取硬核统计数据：龙虎榜、图王、守夜人、早起鸟。
        """
        if self.df.empty:
            return {}

        stats = {}

        # 1. 龙虎榜 (Most Active Users)
        user_counts = self.df[COL_USER_NAME].value_counts().head(top_n)
        stats['top_talkers'] = user_counts.to_dict()

        # 2. 图王争霸 (Most Images)
        # Assuming COL_IMAGE_COUNT exists and is numeric. If not, we might need to count 'image' type messages.
        # Based on parser logic, usually we have image count or type.
        # Let's check COL_IMAGE_COUNT definition in registry. It might not be there.
        # If not, use message type filtering.
        if COL_IMAGE_COUNT in self.df.columns:
            img_counts = self.df.groupby(COL_USER_NAME)[COL_IMAGE_COUNT].sum().sort_values(ascending=False).head(top_n)
            stats['top_img_senders'] = img_counts.to_dict()
        else:
             # Fallback: Count messages where type is 'image'
             # We need to know the column for type. registry says JSON_FIELD_... but DataFrame columns might differ.
             # Usually parser maps it. Let's assume a way to count images.
             # If COL_IMAGE_COUNT is not reliable, we skip or implement fallback.
             # For now, let's assume if it's 0, we try to count '[图片]' in content or check type if available.
             stats['top_img_senders'] = {}

        # 3. 守夜人 (00:00 - 05:00)
        night_mask = (self.df[COL_HOUR] >= 0) & (self.df[COL_HOUR] < 5)
        night_counts = self.df[night_mask][COL_USER_NAME].value_counts().head(top_n)
        stats['night_owls'] = night_counts.to_dict()

        # 4. 早起鸟 (05:00 - 08:00)
        morning_mask = (self.df[COL_HOUR] >= 5) & (self.df[COL_HOUR] < 8)
        morning_counts = self.df[morning_mask][COL_USER_NAME].value_counts().head(top_n)
        stats['early_birds'] = morning_counts.to_dict()

        return stats

    def get_user_rankings(self, top_n: int = DEFAULT_TOP_N) -> Dict[str, pd.DataFrame]:
        """
        生成各类用户排行榜。
        """
        # 意义: 用户行为画像
        # 作用: 计算活跃度、图片发送量、作息习惯等排名
        # 关联: 对应报告中的“龙虎榜”模块
        
        if self.df.empty:
            return {}

        # 1. 话痨榜 (Message Count)
        msg_count = self.df.groupby([COL_USER_ID, COL_USER_NAME]).size().reset_index(name='count')
        msg_rank = msg_count.sort_values('count', ascending=False).head(top_n)
        
        # 2. 图王榜 (Image Sharer)
        img_count = self.df.groupby([COL_USER_ID, COL_USER_NAME])[COL_IMAGE_COUNT].sum().reset_index(name='count')
        img_rank = img_count.sort_values('count', ascending=False).head(top_n)
        
        # 3. 守夜人 (Night Owl: 00:00 - 05:00)
        night_df = self.df[(self.df[COL_HOUR] >= 0) & (self.df[COL_HOUR] < 5)]
        if not night_df.empty:
            night_count = night_df.groupby([COL_USER_ID, COL_USER_NAME]).size().reset_index(name='count')
            night_rank = night_count.sort_values('count', ascending=False).head(top_n)
        else:
            night_rank = pd.DataFrame()

        # 4. 早起鸟 (Early Bird: 05:00 - 08:00)
        morning_df = self.df[(self.df[COL_HOUR] >= 5) & (self.df[COL_HOUR] < 8)]
        if not morning_df.empty:
            morning_count = morning_df.groupby([COL_USER_ID, COL_USER_NAME]).size().reset_index(name='count')
            morning_rank = morning_count.sort_values('count', ascending=False).head(top_n)
        else:
            morning_rank = pd.DataFrame()

        return {
            'message_rank': msg_rank,
            'image_rank': img_rank,
            'night_owl_rank': night_rank,
            'early_bird_rank': morning_rank
        }

    def get_hourly_activity(self) -> pd.DataFrame:
        """
        统计每小时的消息数量。
        """
        # 意义: 时间分布分析
        # 作用: 聚合计算 0-23 点的消息总量，补全缺失的小时
        # 关联: 用于生成热力图或折线图
        
        if self.df.empty:
            return pd.DataFrame({'hour': range(24), 'count': 0})
            
        counts = self.df.groupby(COL_HOUR).size().reset_index(name='count')
        all_hours = pd.DataFrame({'hour': range(24)})
        result = pd.merge(all_hours, counts, on='hour', how='left').fillna(0)
        return result

    def get_daily_activity(self) -> pd.DataFrame:
        """
        统计每日的消息数量。
        """
        if self.df.empty:
            return pd.DataFrame(columns=['date', 'count'])
            
        # Ensure datetime column is datetime type
        if not pd.api.types.is_datetime64_any_dtype(self.df[COL_DATETIME]):
             self.df[COL_DATETIME] = pd.to_datetime(self.df[COL_DATETIME])
             
        daily = self.df.groupby(self.df[COL_DATETIME].dt.date).size().reset_index(name='count')
        daily.columns = ['date', 'count']
        return daily

    def get_word_cloud_data(self, top_n: int = 50) -> List[Tuple[str, int]]:
        """
        提取高频词汇用于生成词云。
        """
        # 意义: 文本内容分析
        # 作用: 对消息内容进行分词、去停用词、统计词频
        # 关联: 依赖 jieba 库，用于生成词云图
        
        if self.df.empty:
            return []
            
        text = " ".join(self.df[COL_CONTENT].dropna().astype(str).tolist())
        
        # 基础停用词 (Phase 1) - 后续可扩展到配置文件
        stop_words = {'的', '了', '是', '我', '你', '在', '他', '我们', '好', '去', '吧', '吗', 
                      '有', '就', '不', '人', '都', '一个', '上', '也', '很', '啊', '哦', '嗯',
                      '哈', '哈哈', '哈哈哈', '图片', '表情', 'video', 'image', 'nan', '[', ']'}
        
        words = jieba.cut(text)
        filtered_words = [w for w in words if len(w) > 1 and w not in stop_words]
        
        return Counter(filtered_words).most_common(top_n)

    def get_quarterly_splits(self) -> Dict[str, pd.DataFrame]:
        """
        智能切分策略：
        1. 首先尝试按自然季度切分。
        2. 检查数据分布是否极度不均（如集中在某一个季度）或时间跨度过短。
        3. 如果满足条件，切换为“等量分块模式”，将数据按消息量均分为 4 份。
        """
        if self.df.empty:
            return {}

        # 确保 datetime 列是 datetime 类型
        if not pd.api.types.is_datetime64_any_dtype(self.df[COL_DATETIME]):
             self.df[COL_DATETIME] = pd.to_datetime(self.df[COL_DATETIME])
        
        # 1. 找到消息最多的年份
        year_counts = self.df[COL_DATETIME].dt.year.value_counts()
        if year_counts.empty:
            return {}
        target_year = year_counts.idxmax()
        self.target_year = target_year 
        
        # 获取时区信息
        tz = self.df[COL_DATETIME].dt.tz

        # 2. 尝试标准季度切分
        q1_start = pd.Timestamp(f"{target_year}-01-01", tz=tz)
        q2_start = pd.Timestamp(f"{target_year}-04-01", tz=tz)
        q3_start = pd.Timestamp(f"{target_year}-07-01", tz=tz)
        q4_start = pd.Timestamp(f"{target_year}-10-01", tz=tz)
        
        splits = {}
        splits['First_quarter'] = self.df[(self.df[COL_DATETIME] >= q1_start) & (self.df[COL_DATETIME] < q2_start)].copy()
        splits['Second_quarter'] = self.df[(self.df[COL_DATETIME] >= q2_start) & (self.df[COL_DATETIME] < q3_start)].copy()
        splits['Third_quarter'] = self.df[(self.df[COL_DATETIME] >= q3_start) & (self.df[COL_DATETIME] < q4_start)].copy()
        splits['Fourth_quarter'] = self.df[(self.df[COL_DATETIME] >= q4_start)].copy()
        
        # 3. 智能检测机制
        total_msgs = len(self.df)
        if total_msgs < 100: # 数据太少不折腾
            return splits
            
        counts = [len(splits[k]) for k in splits]
        max_ratio = max(counts) / total_msgs
        days_covered = (self.df[COL_DATETIME].max() - self.df[COL_DATETIME].min()).days
        
        # 触发条件：
        # A. 某一季度占据超过 80% 的数据 (极度偏科)
        # B. 时间跨度小于 9 个月 (270天) 且非空 (避免刚好跨年的情况被误判，主要针对短时间记录)
        #    注意：如果是跨年数据，days_covered 可能很大，但这里只取了 target_year 的切分。
        #    更严谨的是看 target_year 内的跨度。
        #    简单起见，如果 max_ratio > 0.8，说明季度切分失效。
        
        is_concentrated = max_ratio > 0.8
        is_short_duration = days_covered < 200 # 约半年多一点
        
        if is_concentrated or is_short_duration:
            # 切换到动态等量切分
            return self._get_dynamic_splits(4)
            
        return splits

    def _get_dynamic_splits(self, n_splits: int = 4) -> Dict[str, pd.DataFrame]:
        """
        将 DataFrame 按消息数量均分为 n 份。
        """
        if self.df.empty:
            return {}
            
        # 确保按时间排序
        df_sorted = self.df.sort_values(COL_DATETIME)
        total = len(df_sorted)
        chunk_size = total // n_splits
        
        splits = {}
        for i in range(n_splits):
            start_idx = i * chunk_size
            # 最后一个分块包含剩余所有
            if i == n_splits - 1:
                end_idx = total
            else:
                end_idx = (i + 1) * chunk_size
                
            chunk = df_sorted.iloc[start_idx:end_idx].copy()
            
            if chunk.empty:
                time_range_str = "No Data"
            else:
                start_date = chunk[COL_DATETIME].min().strftime("%m.%d")
                end_date = chunk[COL_DATETIME].max().strftime("%m.%d")
                time_range_str = f"{start_date}-{end_date}"
            
            # 使用 Period_X 作为 key，并附带时间范围供 LLM 理解
            key_name = f"Period_{i+1} ({time_range_str})"
            splits[key_name] = chunk
            
        return splits

    def get_target_year(self) -> int:
        """
        获取分析的基准年份。
        """
        if hasattr(self, 'target_year'):
            return self.target_year
        elif not self.df.empty:
            if not pd.api.types.is_datetime64_any_dtype(self.df[COL_DATETIME]):
                self.df[COL_DATETIME] = pd.to_datetime(self.df[COL_DATETIME])
            return self.df[COL_DATETIME].dt.year.mode()[0]
        else:
            return pd.Timestamp.now().year

    def calculate_message_density(self, window_size: str = '1min') -> pd.DataFrame:
        """
        计算时间窗口内的消息密度。
        """
        # 意义: 密度分析
        # 作用: 统计单位时间内的消息数量，用于识别热点时刻
        # 关联: Phase 2 Level 3 采样策略依赖此数据提取高密度窗口
        
        if self.df.empty:
            return pd.DataFrame()
            
        # 设置时间索引
        temp_df = self.df.set_index(COL_DATETIME)
        # 重采样计数
        density = temp_df.resample(window_size).size().reset_index(name='count')
        return density

    def adaptive_sample(self, max_tokens: int = 4000, logger=None) -> str:
        """
        实现 Phase 2 - 3.3 自适应多级采样路由策略。
        
        Args:
            max_tokens: LLM 上下文限制（Token数）
            logger: 日志记录器
        
        Returns:
            str: 最终采样并压缩后的文本字符串
        """
        # 1. 格式压缩 (Format Minification)
        # 将 DataFrame 转换为紧凑格式，并合并连续发言
        compressed_msgs = self._compress_messages()
        
        if not compressed_msgs:
            return ""

        # 2. 估算 Token (1 Token ≈ 1.5 chars for Chinese context, conservative estimate)
        # Let's calculate total characters first
        total_chars = sum(len(m['text']) for m in compressed_msgs)
        estimated_tokens = int(total_chars / 1.5)
        
        # 3. 路由判断 (Router)
        # Level 1: 无损模式 (Lossless) - Token < 80% 窗口
        if estimated_tokens < max_tokens * 0.8:
            if logger: logger.info(f"Level 1 (无损): 估算Token {estimated_tokens} < {max_tokens*0.8}，全量发送")
            return "\n".join([m['text'] for m in compressed_msgs])
            
        # Level 2: 轻度压缩 (Light Compression) - 略超窗口
        # 过滤无意义单字回复和纯表情
        filtered_msgs = self._filter_noise(compressed_msgs)
        total_chars_l2 = sum(len(m['text']) for m in filtered_msgs)
        estimated_tokens_l2 = int(total_chars_l2 / 1.5)
        
        if estimated_tokens_l2 < max_tokens:
            if logger: logger.info(f"Level 2 (轻度压缩): 过滤后Token {estimated_tokens_l2} < {max_tokens}，发送过滤版")
            return "\n".join([m['text'] for m in filtered_msgs])

        # Level 3: 智能聚焦 (Smart Focus) - Token 严重超出 (> 1.5倍窗口)
        # 提取高密度窗口 + 稀疏背景
        if logger: logger.info(f"Level 3 (智能聚焦): Token {estimated_tokens_l2} > {max_tokens}，启动密度采样")
        return self._smart_focus_sample(compressed_msgs, max_tokens, logger)

    def _compress_messages(self) -> List[Dict[str, Any]]:
        """
        执行格式压缩：
        1. 格式化为 [MM-DD HH:mm] Name: Content
        2. 合并同一用户 1 分钟内的连续发言
        """
        if self.df.empty:
            return []

        # 确保按时间排序
        df_sorted = self.df.sort_values(COL_DATETIME)
        
        results = []
        current_group = None
        
        for _, row in df_sorted.iterrows():
            timestamp = row[COL_DATETIME]
            user_name = row.get(COL_USER_NAME, 'Unknown')
            content = str(row.get(COL_CONTENT, '')).strip()
            
            # Skip empty content
            if not content:
                continue

            # Check if we can merge with previous
            if current_group:
                prev_time = current_group['last_time']
                prev_user = current_group['user']
                
                # 同一用户且间隔小于1分钟
                time_diff = (timestamp - prev_time).total_seconds()
                if user_name == prev_user and time_diff < 60:
                    current_group['contents'].append(content)
                    current_group['last_time'] = timestamp
                    continue
            
            # Save previous group
            if current_group:
                results.append(self._format_group(current_group))
            
            # Start new group
            current_group = {
                'start_time': timestamp,
                'last_time': timestamp,
                'user': user_name,
                'contents': [content]
            }
            
        # Save last group
        if current_group:
            results.append(self._format_group(current_group))
            
        return results

    def _format_group(self, group) -> Dict[str, Any]:
        """格式化单个消息组"""
        time_str = group['start_time'].strftime("%m-%d %H:%M")
        merged_content = " | ".join(group['contents'])
        # 截断过长消息
        if len(merged_content) > 200:
            merged_content = merged_content[:200] + "..."
            
        formatted_text = f"[{time_str}] {group['user']}: {merged_content}"
        return {
            'time': group['start_time'],
            'text': formatted_text,
            'len': len(formatted_text)
        }

    def _filter_noise(self, msgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Level 2: 过滤噪音 (单字、无意义回复)"""
        filtered = []
        noise_words = {'1', '6', '嗯', '哦', '哈', '啊', '是', '好的', 'ok', 'OK'}
        
        for m in msgs:
            content_part = m['text'].split(':', 1)[1].strip()
            # 过滤单字噪音
            if content_part in noise_words:
                continue
            # 过滤纯符号/表情 (简单判断: 长度<2且非中文)
            # 这里简化处理，保留大部分
            filtered.append(m)
        return filtered

    def _smart_focus_sample(self, msgs: List[Dict[str, Any]], max_tokens: int, logger) -> str:
        """
        Level 3: 基于密度的智能采样
        1. 计算密度，提取 Top N 热点窗口
        2. 热点窗口内保留全部/大部分
        3. 非热点窗口稀疏采样
        """
        if not msgs:
            return ""

        # Target chars
        target_chars = int(max_tokens * 1.5)
        
        # 1. 转换为 DataFrame 以方便时间窗口计算
        times = [m['time'] for m in msgs]
        df_temp = pd.DataFrame({'time': times, 'msg': msgs})
        df_temp.set_index('time', inplace=True)
        
        # 2. 计算 10分钟 窗口的消息量
        density = df_temp.resample('10min').count()
        
        # 3. 找出 Top 20 热点窗口
        top_windows = density.sort_values('msg', ascending=False).head(20).index
        
        # 标记每条消息是否在热点窗口内
        final_selection = []
        # 将热点窗口转为 set 以便快速查找 (简单起见，按整点比较)
        # 这里使用一个简单策略：遍历消息，如果它属于某个 Top 窗口，则标记为 Hot
        
        # 为了高效，我们可以给 df_temp 加一列 is_hot
        df_temp['is_hot'] = False
        for window_start in top_windows:
            window_end = window_start + pd.Timedelta(minutes=10)
            # 标记窗口内的消息
            mask = (df_temp.index >= window_start) & (df_temp.index < window_end)
            df_temp.loc[mask, 'is_hot'] = True
            
        # 4. 采样
        # 热点区域：保留 (如果总量还是太大，可能需要进一步压缩，这里暂定全保留)
        # 非热点区域：1/10 采样 (或者根据剩余空间动态计算)
        
        # 估算热点区域大小
        hot_msgs = df_temp[df_temp['is_hot']]['msg'].tolist()
        hot_chars = sum(len(m['text']) for m in hot_msgs)
        
        remaining_budget = target_chars - hot_chars
        
        if remaining_budget < 0:
            # 热点都装不下，只取热点的前部分或 Top 10 窗口
            if logger: logger.info("热点数据过多，仅保留热点窗口")
            selected_msgs = hot_msgs
        else:
            # 还有预算，填充非热点数据
            cold_msgs = df_temp[~df_temp['is_hot']]['msg'].tolist()
            if not cold_msgs:
                selected_msgs = hot_msgs
            else:
                cold_chars = sum(len(m['text']) for m in cold_msgs)
                if cold_chars <= remaining_budget:
                    # 全装下
                    selected_msgs = hot_msgs + cold_msgs
                else:
                    # 均匀采样冷数据
                    step = int(cold_chars / max(1, remaining_budget)) + 1
                    sampled_cold = cold_msgs[::step]
                    selected_msgs = hot_msgs + sampled_cold
        
        # 重新按时间排序
        selected_msgs.sort(key=lambda x: x['time'])
        
        return "\n".join([m['text'] for m in selected_msgs])
