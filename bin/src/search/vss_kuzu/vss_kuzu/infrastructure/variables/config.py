#!/usr/bin/env python3
"""
設定管理モジュール

アプリケーション設定の統合管理と優先順位処理を提供
優先順位: 引数 > 環境変数 > デフォルト値
"""

from typing import Optional, Dict, Any, TypedDict

from .env import load_environment_variables, EnvironmentVariables


class VSSConfig(TypedDict):
    """VSS（Vector Similarity Search）の統合設定"""
    # データベース設定
    db_path: str
    in_memory: bool
    
    # 埋め込みモデル設定
    model_name: str
    embedding_dimension: int
    
    # VECTOR拡張設定
    vector_extension_timeout: int
    
    # HNSWインデックス設定
    index_mu: int
    index_ml: int
    index_metric: str
    index_efc: int
    
    # 検索設定
    search_efs: int
    default_limit: int
    
    # 設定のソース情報（デバッグ用）
    _sources: Dict[str, str]


def create_config(
    db_path: Optional[str] = None,
    in_memory: Optional[bool] = None,
    model_name: Optional[str] = None,
    embedding_dimension: Optional[int] = None,
    vector_extension_timeout: Optional[int] = None,
    index_mu: Optional[int] = None,
    index_ml: Optional[int] = None,
    index_metric: Optional[str] = None,
    index_efc: Optional[int] = None,
    search_efs: Optional[int] = None,
    default_limit: Optional[int] = None
) -> VSSConfig:
    """
    引数、環境変数、デフォルト値を統合して設定を作成
    
    Args:
        db_path: データベースパス
        in_memory: インメモリモード
        model_name: 埋め込みモデル名
        embedding_dimension: 埋め込みベクトルの次元数
        vector_extension_timeout: VECTOR拡張のタイムアウト秒数
        index_mu: HNSWインデックスのmu値
        index_ml: HNSWインデックスのml値
        index_metric: 距離計算メトリック
        index_efc: インデックス構築時の候補数
        search_efs: 検索時の候補数
        default_limit: デフォルトの検索結果数
        
    Returns:
        統合された設定オブジェクト
    """
    # 環境変数を読み込む
    env_vars = load_environment_variables()
    
    # 優先順位に従って値を決定（引数 > 環境変数）
    sources = {}
    
    # データベース設定
    final_db_path = db_path if db_path is not None else env_vars['vss_db_path']
    sources['db_path'] = 'argument' if db_path is not None else 'environment'
    
    final_in_memory = in_memory if in_memory is not None else env_vars['vss_in_memory']
    sources['in_memory'] = 'argument' if in_memory is not None else 'environment'
    
    # 埋め込みモデル設定
    final_model_name = model_name if model_name is not None else env_vars['vss_model_name']
    sources['model_name'] = 'argument' if model_name is not None else 'environment'
    
    final_embedding_dimension = embedding_dimension if embedding_dimension is not None else env_vars['vss_embedding_dimension']
    sources['embedding_dimension'] = 'argument' if embedding_dimension is not None else 'environment'
    
    # VECTOR拡張設定
    final_vector_extension_timeout = vector_extension_timeout if vector_extension_timeout is not None else env_vars['vss_vector_extension_timeout']
    sources['vector_extension_timeout'] = 'argument' if vector_extension_timeout is not None else 'environment'
    
    # HNSWインデックス設定
    final_index_mu = index_mu if index_mu is not None else env_vars['vss_index_mu']
    sources['index_mu'] = 'argument' if index_mu is not None else 'environment'
    
    final_index_ml = index_ml if index_ml is not None else env_vars['vss_index_ml']
    sources['index_ml'] = 'argument' if index_ml is not None else 'environment'
    
    final_index_metric = index_metric if index_metric is not None else env_vars['vss_index_metric']
    sources['index_metric'] = 'argument' if index_metric is not None else 'environment'
    
    final_index_efc = index_efc if index_efc is not None else env_vars['vss_index_efc']
    sources['index_efc'] = 'argument' if index_efc is not None else 'environment'
    
    # 検索設定
    final_search_efs = search_efs if search_efs is not None else env_vars['vss_search_efs']
    sources['search_efs'] = 'argument' if search_efs is not None else 'environment'
    
    final_default_limit = default_limit if default_limit is not None else env_vars.get('vss_default_limit', 10)
    sources['default_limit'] = 'argument' if default_limit is not None else 'environment'
    
    return {
        'db_path': final_db_path,
        'in_memory': final_in_memory,
        'model_name': final_model_name,
        'embedding_dimension': final_embedding_dimension,
        'vector_extension_timeout': final_vector_extension_timeout,
        'index_mu': final_index_mu,
        'index_ml': final_index_ml,
        'index_metric': final_index_metric,
        'index_efc': final_index_efc,
        'search_efs': final_search_efs,
        'default_limit': final_default_limit,
        '_sources': sources
    }


def get_default_config() -> VSSConfig:
    """
    デフォルト設定（環境変数を含む）を取得
    
    Returns:
        デフォルト設定オブジェクト
    """
    return create_config()


def merge_config(base_config: VSSConfig, **overrides) -> VSSConfig:
    """
    既存の設定に部分的な変更を適用
    
    Args:
        base_config: ベースとなる設定
        **overrides: 上書きする設定値
        
    Returns:
        マージされた設定オブジェクト
    """
    # 上書きされたフィールドのソース情報を更新
    new_sources = base_config.get('_sources', {}).copy() if base_config.get('_sources') else {}
    for key in overrides:
        if key in new_sources:
            new_sources[key] = 'override'
    
    # 新しい設定辞書を作成
    new_config = base_config.copy()
    new_config.update(overrides)
    new_config['_sources'] = new_sources
    return new_config


def validate_config(config: VSSConfig) -> None:
    """
    設定値の妥当性を検証
    
    Args:
        config: 検証する設定オブジェクト
        
    Raises:
        ValueError: 設定値が不正な場合
    """
    # 埋め込み次元数の検証
    if config['embedding_dimension'] <= 0:
        raise ValueError(f"埋め込み次元数は正の整数である必要があります: {config['embedding_dimension']}")
    
    # HNSWパラメータの検証
    if config['index_mu'] <= 0:
        raise ValueError(f"index_muは正の整数である必要があります: {config['index_mu']}")
    
    if config['index_ml'] <= 0:
        raise ValueError(f"index_mlは正の整数である必要があります: {config['index_ml']}")
    
    if config['index_ml'] < config['index_mu']:
        raise ValueError(f"index_ml ({config['index_ml']}) はindex_mu ({config['index_mu']}) 以上である必要があります")
    
    # メトリックの検証
    valid_metrics = {'cosine', 'l2', 'l2sq', 'dotproduct'}
    if config['index_metric'] not in valid_metrics:
        raise ValueError(f"index_metricは {valid_metrics} のいずれかである必要があります: {config['index_metric']}")
    
    # タイムアウトの検証
    if config['vector_extension_timeout'] <= 0:
        raise ValueError(f"vector_extension_timeoutは正の整数である必要があります: {config['vector_extension_timeout']}")


def config_to_dict(config: VSSConfig) -> Dict[str, Any]:
    """
    設定オブジェクトを辞書に変換
    
    Args:
        config: 設定オブジェクト
        
    Returns:
        設定値の辞書
    """
    # _sources フィールドを除いたコピーを返す
    result = config.copy()
    result.pop('_sources', None)
    return result