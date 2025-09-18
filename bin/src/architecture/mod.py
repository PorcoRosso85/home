"""
Architecture Module - Public API

このモジュールの公開APIです。外部からの利用者はこのファイルのみを参照してください。

規約:
- モジュール内の公開APIを一元エクスポート
- 外部利用者はこのファイル経由のみでアクセス
- 型情報を含む公開APIを提供
"""

# Configuration and Environment Variables
from .variables import (
    ArchitectureConfig,
    get_config,
    get_database_url,
    get_log_level,
    get_data_directory,
)

# Application Layer - ユースケース層
# 将来的に application/ ディレクトリ内のモジュールを追加予定
# from .application import ...

# Domain Layer - ビジネスロジック層  
# 将来的に domain/ ディレクトリ内のモジュールを追加予定
# from .domain import ...

# 公開API一覧
__all__ = [
    # Configuration Types
    'ArchitectureConfig',
    
    # Configuration Functions
    'get_config',
    'get_database_url',
    'get_log_level', 
    'get_data_directory',
    
    # Application Layer
    # 将来追加予定
    
    # Domain Layer
    # 将来追加予定
]


def get_version() -> str:
    """モジュールのバージョンを取得します"""
    return "0.1.0"


def get_module_info() -> dict:
    """モジュールの情報を取得します"""
    return {
        'name': 'architecture',
        'version': get_version(),
        'description': 'Architecture module with DDD and Hexagonal Architecture principles',
        'layers': ['application', 'domain', 'infrastructure'],
        'public_api': __all__,
    }