"""
クエリ実行コマンドモジュール

Cypherクエリを実行する機能を提供します。
"""

import json
from typing import Dict, Any, List, Optional

from upsert.application.query_service import handle_query_command as app_handle_query
from upsert.interface.commands.utils import parse_param_strings, get_default_db_path, is_in_memory_mode


def handle_query(query: str, param_strings: Optional[List[str]] = None,
                       db_path: Optional[str] = None, in_memory: Optional[bool] = None,
                       validation_level: str = "standard", pretty: bool = True) -> Dict[str, Any]:
    """
    Cypherクエリを実行するコマンドを処理する
    
    Args:
        query: 実行するCypherクエリ
        param_strings: クエリパラメータ（"name=value"形式の文字列のリスト）
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        validation_level: 検証レベル（"none", "standard", "strict"）
        pretty: 結果を整形して表示するかどうか
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # デフォルト値の適用
    if db_path is None:
        db_path = get_default_db_path()
    
    if in_memory is None:
        in_memory = is_in_memory_mode()
    
    # パラメータ文字列をパース
    params = parse_param_strings(param_strings or [])
    
    # クエリサービスを呼び出し
    result = app_handle_query(
        query=query,
        param_strings=param_strings or [],
        db_path=db_path,
        in_memory=in_memory,
        validation_level=validation_level
    )
    
    # 結果の表示
    display_query_result(result, pretty)
    
    return result


def display_query_result(result: Dict[str, Any], pretty: bool = True) -> None:
    """
    クエリ実行結果を表示
    
    Args:
        result: クエリ実行結果
        pretty: 整形して表示するかどうか
    """
    validation = result.get("validation", {})
    if validation.get("is_valid", False):
        print("✅ クエリは検証に成功しました")
    else:
        print("❌ クエリはSHACL検証に失敗しました:")
        print(f"  {validation.get('report', '不明なエラー')}")
        
    execution = result.get("execution", {})
    if execution.get("success", False):
        print("\n📊 クエリ実行結果:")
        
        stats = execution.get("stats", {})
        if stats:
            print(f"  実行時間: {stats.get('execution_time_ms', 0)}ms")
            print(f"  影響を受けた行数: {stats.get('affected_rows', 0)}")
        
        data = execution.get("data", [])
        if data:
            try:
                if pretty:
                    # データをJSON形式で整形表示
                    formatted_data = json.dumps(data, indent=2, ensure_ascii=False)
                    print(f"\n{formatted_data}")
                else:
                    # 簡易表示
                    if isinstance(data, list):
                        for i, item in enumerate(data, 1):
                            print(f"  {i}. {item}")
                    else:
                        print(f"  データ: {data}")
            except Exception as e:
                print(f"  [データの表示エラー: {str(e)}]")
    else:
        print(f"\n❌ クエリ実行エラー: {execution.get('message', '不明なエラー')}")
