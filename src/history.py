# src/history.py

"""
History Manager Module
======================
负责管理分析历史记录，支持持久化存储。
遵循 Phase 5 编程规范。
"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

HISTORY_FILE = "history.json"

class HistoryManager:
    """
    历史记录管理器，处理记录的增删查改。
    """
    
    def __init__(self, file_path: str = HISTORY_FILE):
        # 意义: 初始化管理器
        # 作用: 确定存储路径，确保文件存在
        # 关联: 被 App 调用
        self.file_path = file_path
        self._ensure_file()

    def _ensure_file(self):
        """确保历史记录文件存在。"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def add_record(self, chat_name: str, messages_count: int, report_path: str):
        """
        添加一条新的分析记录。
        """
        # 意义: 记录分析结果
        # 作用: 保存元数据和报告路径
        # 关联: 分析完成后调用
        
        record = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chat_name": chat_name,
            "messages_count": messages_count,
            "report_path": report_path
        }
        
        records = self.get_records()
        records.insert(0, record) # 最新记录排前面
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def get_records(self) -> List[Dict]:
        """
        获取所有历史记录。
        """
        # 意义: 读取历史
        # 作用: 用于前端展示
        # 关联: 历史记录侧边栏
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def clear_history(self):
        """清空历史记录。"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
