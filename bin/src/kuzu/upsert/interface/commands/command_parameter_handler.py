"""
コマンドパラメータハンドラーモジュール

コマンド実行に共通して使用されるパラメータ処理と接続管理関数を提供します。
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional, Union, Tuple


def parse_param_string(param_string: str) -> Tuple[str, Any]:
    """
    パラメータ文字列をパースする
    
    Args:
        param_string: "name=value"形式のパラメータ文字列
        
    Returns:
        Tuple[str, Any]: パラメータ名と値のタプル
    
    Raises:
        ValueError: パラメータ文字列の形式が不正な場合
    """
    if '=' not in param_string:
        raise ValueError(f"パラメータは 'name=value' 形式で指定してください: {param_string}")
    
    name, value = param_string.split('=', 1)
    
    # 値を適切な型に変換する
    if value.lower() == 'true':
        value = True
    elif value.lower() == 'false':
        value = False
    elif value.lower() == 'null':
        value = None
    else:
        try:
            # 整数に変換を試みる
            value = int(value)
        except ValueError:
            try:
                # 浮動小数点数に変換を試みる
                value = float(value)
            except ValueError:
                # 文字列のまま
                pass
    
    return name, value


def parse_param_strings(param_strings: List[str]) -> Dict[str, Any]:
    """
    パラメータ文字列のリストをパースする
    
    Args:
        param_strings: "name=value"形式のパラメータ文字列のリスト
        
    Returns:
        Dict[str, Any]: パラメータ名と値のマッピング
    """
    params = {}
    
    if not param_strings:
        return params
    
    for param_string in param_strings:
        try:
            name, value = parse_param_string(param_string)
            params[name] = value
        except ValueError as e:
            print(f"警告: {e}", file=sys.stderr)
    
    return params


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    JSONファイルを読み込む
    
    Args:
        file_path: ファイルパス
        
    Returns:
        Dict[str, Any]: JSON内容
        
    Raises:
        FileNotFoundError: ファイルが存在しない場合
        json.JSONDecodeError: JSONの形式が不正な場合
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_result(result: Dict[str, Any], pretty: bool = True) -> str:
    """
    結果を整形して文字列に変換する
    
    Args:
        result: 結果データ
        pretty: 整形するかどうか
        
    Returns:
        str: 整形された結果文字列
    """
    if pretty:
        return json.dumps(result, indent=2, ensure_ascii=False)
    else:
        return json.dumps(result, ensure_ascii=False)


def get_default_db_path() -> str:
    """
    デフォルトのデータベースパスを取得する
    
    Returns:
        str: デフォルトのデータベースパス
    """
    from upsert.infrastructure.variables import DB_DIR
    return DB_DIR


def is_in_memory_mode() -> bool:
    """
    インメモリモードかどうかを判定する
    
    Returns:
        bool: インメモリモードならTrue
    """
    from upsert.infrastructure.variables import DEFAULT_IN_MEMORY
    return DEFAULT_IN_MEMORY


def get_connection(db_path: Optional[str] = None, in_memory: Optional[bool] = None, 
                 with_query_loader: bool = True) -> Dict[str, Any]:
    """
    データベース接続を取得する
    
    Args:
        db_path: データベースパス
        in_memory: インメモリモードかどうか
        with_query_loader: クエリローダーを使用するかどうか
        
    Returns:
        Dict[str, Any]: 接続情報または接続エラー
    """
    from upsert.infrastructure.database.connection import get_connection as db_get_connection
    
    # デフォルト値の適用
    if db_path is None:
        db_path = get_default_db_path()
    
    if in_memory is None:
        in_memory = is_in_memory_mode()
    
    return db_get_connection(db_path=db_path, with_query_loader=with_query_loader, in_memory=in_memory)