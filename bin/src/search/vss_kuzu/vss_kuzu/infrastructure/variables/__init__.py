#!/usr/bin/env python3
"""
外部依存・外部入力統合管理モジュール

環境変数、設定ファイル、引数などの外部入力を統合管理
"""

from .env import (
    EnvironmentVariables,
    load_environment_variables,
    get_current_environment,
    get_env_str,
    get_env_int,
    get_env_bool
)

from .config import (
    VSSConfig,
    create_config,
    get_default_config,
    merge_config,
    validate_config,
    config_to_dict
)

__all__ = [
    # Environment
    'EnvironmentVariables',
    'load_environment_variables',
    'get_current_environment',
    'get_env_str',
    'get_env_int',
    'get_env_bool',
    # Config
    'VSSConfig',
    'create_config',
    'get_default_config',
    'merge_config',
    'validate_config',
    'config_to_dict'
]