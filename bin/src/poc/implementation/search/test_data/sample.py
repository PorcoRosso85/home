"""Sample Python file for testing"""

import os
from typing import List, Dict

# 定数定義
MAX_ITEMS = 100
DEFAULT_NAME = "test"

# 変数定義
counter = 0


class SampleClass:
    """サンプルクラス"""
    
    def __init__(self, name: str):
        self.name = name
    
    def get_name(self) -> str:
        """名前を取得"""
        return self.name


def sample_function(items: List[str]) -> Dict[str, int]:
    """サンプル関数"""
    result = {}
    for item in items:
        result[item] = len(item)
    return result


# 型エイリアス
ItemDict = Dict[str, int]