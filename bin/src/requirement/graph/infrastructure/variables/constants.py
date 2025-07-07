"""
定数定義モジュール

アプリケーション全体で使用される定数を定義します。
これらの値は変更不可で、コンパイル時に確定します。
"""
from typing import Dict, List

# 埋め込み関連
EMBEDDING_DIM = 50

# グラフ制約関連
MAX_GRAPH_DEPTH = 10  # プロジェクトで設定可能な最大グラフ深さ

# ログレベル定義
LOG_LEVELS = {
    'TRACE': 0,
    'DEBUG': 1,
    'INFO': 2,
    'WARN': 3,
    'ERROR': 4
}

# レイヤー優先度定義（最適化機能用）
LAYER_PRIORITY = {
    "database": 1,
    "infrastructure": 2,
    "domain": 3,
    "api": 4,
    "service": 5,
    "ui": 6,
    "frontend": 7
}

# 自律的分解関連
AUTONOMOUS_MAX_DEPTH = 3  # 自律的分解の最大深度
AUTONOMOUS_TARGET_SIZE = 5  # 各レベルでの目標子要件数

# 検索関連
DEFAULT_SEARCH_THRESHOLD = 0.5  # 類似検索のデフォルト閾値
DEFAULT_SEARCH_LIMIT = 10  # 検索結果の最大数