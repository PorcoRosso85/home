"""
システム変数モジュール

このモジュールでは、アプリケーション全体で使用される設定変数を定義します。
デフォルト値は使用せず、すべての設定はここで明示的に行います。
"""

import os

# ディレクトリ設定
# プロジェクトルートの絶対パスを取得
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
QUERY_DIR = os.path.join(ROOT_DIR, "query")  # クエリディレクトリの絶対パス
INIT_DIR = os.path.join(QUERY_DIR, "init")   # 初期化ディレクトリの絶対パス

# ファイルパス設定
SHAPES_FILE = os.path.join(ROOT_DIR, "design_shapes.ttl")   # SHACLシェイプファイルのパス
BASE_SHAPES_FILE = os.path.join(ROOT_DIR, "infrastructure", "schemas", "base_shapes.ttl")  # 基本シェイプファイルのパス

# データベース関連の設定
DB_DIR = "/tmp/kuzudb"  # デフォルトのデータベースディレクトリ
DEFAULT_IN_MEMORY = False  # デフォルトはディスクモード

# ロギング関連の設定
LOG_LEVEL = 0  # 0: DEBUG, 1: INFO, 2: WARNING, 3: ERROR

# 初期化サービス関連の設定
MAX_TREE_DEPTH = 100  # ツリー構造の最大再帰深度
DEFAULT_MAX_RETRIES = 3  # 最大リトライ回数
SYNC_WAIT_TIME = 0.5  # データベース同期待機時間(秒)
RETRY_WAIT_TIMES = [0.5, 1.0, 2.0]  # リトライ間隔(秒)

# ファイルチェック関連の設定
SUPPORTED_FILE_FORMATS = [".yml", ".yaml", ".json", ".csv"]
