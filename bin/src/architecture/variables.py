"""
Environment Variables and Configuration Management

環境変数および設定値を管理するモジュールです。

規約:
- グローバル状態の禁止（関数として提供）
- デフォルト値の禁止（必須変数は明示的にエラー）
- 型安全性の確保（TypedDictで定義）
"""

import os
from typing import TypedDict


class ArchitectureConfig(TypedDict):
    """Architecture module configuration type definition"""
    database_url: str
    log_level: str
    data_directory: str


def get_config() -> ArchitectureConfig:
    """
    環境変数から設定を取得します。
    
    必須の環境変数が設定されていない場合は明示的にエラーを発生させます。
    デフォルト値は提供しません。
    
    Returns:
        ArchitectureConfig: 型安全な設定辞書
        
    Raises:
        ValueError: 必須環境変数が未設定の場合
    """
    required_vars = {
        'ARCHITECTURE_DATABASE_URL': 'database_url',
        'ARCHITECTURE_LOG_LEVEL': 'log_level', 
        'ARCHITECTURE_DATA_DIRECTORY': 'data_directory'
    }
    
    config = {}
    missing_vars = []
    
    for env_var, config_key in required_vars.items():
        value = os.getenv(env_var)
        if value is None:
            missing_vars.append(env_var)
        else:
            config[config_key] = value
    
    if missing_vars:
        raise ValueError(
            f"Required environment variables are not set: {', '.join(missing_vars)}"
        )
    
    return ArchitectureConfig(config)


def get_database_url() -> str:
    """データベースURLを取得します"""
    return get_config()['database_url']


def get_log_level() -> str:
    """ログレベルを取得します"""
    return get_config()['log_level']


def get_data_directory() -> str:
    """データディレクトリパスを取得します"""
    return get_config()['data_directory']