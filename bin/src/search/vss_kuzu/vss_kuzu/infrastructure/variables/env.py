#!/usr/bin/env python3
"""
環境変数管理モジュール

環境変数の読み取り、検証、デフォルト値の提供を担当
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentVariables:
    """環境変数の設定値を保持する不変データクラス"""
    vss_db_path: str
    vss_model_name: str
    vss_embedding_dimension: int
    vss_in_memory: bool
    vss_vector_extension_timeout: int
    vss_index_mu: int
    vss_index_ml: int
    vss_index_metric: str
    vss_index_efc: int
    vss_search_efs: int


def get_env_str(key: str, default: str) -> str:
    """
    環境変数を文字列として取得
    
    Args:
        key: 環境変数名
        default: デフォルト値
        
    Returns:
        環境変数の値またはデフォルト値
    """
    return os.environ.get(key, default)


def get_env_int(key: str, default: int) -> int:
    """
    環境変数を整数として取得
    
    Args:
        key: 環境変数名
        default: デフォルト値
        
    Returns:
        環境変数の値またはデフォルト値
        
    Raises:
        ValueError: 環境変数が整数に変換できない場合
    """
    value = os.environ.get(key)
    if value is None:
        return default
    
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"環境変数 {key} の値 '{value}' は整数に変換できません")


def get_env_bool(key: str, default: bool) -> bool:
    """
    環境変数をブール値として取得
    
    Args:
        key: 環境変数名
        default: デフォルト値
        
    Returns:
        環境変数の値またはデフォルト値
    """
    value = os.environ.get(key)
    if value is None:
        return default
    
    # 'true', '1', 'yes', 'on' を True として扱う（大文字小文字を区別しない）
    return value.lower() in ('true', '1', 'yes', 'on')


def load_environment_variables() -> EnvironmentVariables:
    """
    環境変数を読み込んで設定オブジェクトを作成
    
    Returns:
        環境変数の設定オブジェクト
    """
    return EnvironmentVariables(
        # データベース設定
        vss_db_path=get_env_str('VSS_DB_PATH', './kuzu_db'),
        vss_in_memory=get_env_bool('VSS_IN_MEMORY', False),
        
        # 埋め込みモデル設定
        vss_model_name=get_env_str('VSS_MODEL_NAME', 'cl-nagoya/ruri-v3-30m'),
        vss_embedding_dimension=get_env_int('VSS_EMBEDDING_DIMENSION', 256),
        
        # VECTOR拡張設定
        vss_vector_extension_timeout=get_env_int('VSS_VECTOR_EXTENSION_TIMEOUT', 30),
        
        # HNSWインデックス設定
        vss_index_mu=get_env_int('VSS_INDEX_MU', 30),
        vss_index_ml=get_env_int('VSS_INDEX_ML', 60),
        vss_index_metric=get_env_str('VSS_INDEX_METRIC', 'cosine'),
        vss_index_efc=get_env_int('VSS_INDEX_EFC', 200),
        
        # 検索設定
        vss_search_efs=get_env_int('VSS_SEARCH_EFS', 200)
    )


def get_current_environment() -> Dict[str, Any]:
    """
    現在の環境変数設定を辞書形式で取得
    
    Returns:
        環境変数の設定辞書
    """
    env_vars = load_environment_variables()
    return {
        'db_path': env_vars.vss_db_path,
        'in_memory': env_vars.vss_in_memory,
        'model_name': env_vars.vss_model_name,
        'embedding_dimension': env_vars.vss_embedding_dimension,
        'vector_extension_timeout': env_vars.vss_vector_extension_timeout,
        'index_mu': env_vars.vss_index_mu,
        'index_ml': env_vars.vss_index_ml,
        'index_metric': env_vars.vss_index_metric,
        'index_efc': env_vars.vss_index_efc,
        'search_efs': env_vars.vss_search_efs
    }