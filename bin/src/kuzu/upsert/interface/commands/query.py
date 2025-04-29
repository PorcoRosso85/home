"""
クエリ実行コマンドモジュール

Cypherクエリを実行する機能を提供します。
"""

import json
from typing import Dict, Any, List, Optional

from upsert.application.query_service import handle_query_command as app_handle_query
from upsert.interface.commands.utils import parse_param_strings, get_default_db_path, is_in_memory_mode


def handle_query(query: str = None, param_strings: Optional[List[str]] = None,
                       db_path: Optional[str] = None, in_memory: Optional[bool] = None,
                       validation_level: str = "standard", pretty: bool = True) -> Dict[str, Any]:
    """
    Cypherクエリを実行するコマンドを処理する
    
    Kuzuデータベースに対してCypherクエリを実行します。
    基本的なノードクエリから複雑な関係検索まで様々なクエリを実行できます。
    
    基本的なノードクエリ例:
    - MATCH (n) RETURN n                    # データベース内のすべてのノードを取得
    - MATCH (n:Function) RETURN n           # 特定のラベルを持つノードのみを取得
    - MATCH (n) RETURN n.id, n.name         # ノードの特定プロパティのみを取得
    - MATCH (n) WHERE n.age > 30 RETURN n   # 条件でフィルタリング
    - MATCH (n) RETURN n LIMIT 100          # 結果を制限する
    - MATCH (n:Function)-[:HAS_PARAMETER]->(p:ParameterType) RETURN n, p  # 関係を持つノードを取得
    
    パラメータを使用する例:
    - MATCH (n) WHERE n.property = $value RETURN n  # --param value=search_term を使用
    
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
    
    # "help"の場合はヘルプを表示
    if query == "help" or query and query.lower() == "help":
        from upsert.application.help_service import get_query_help
        
        # キーワードが指定されていなければ基本ヘルプを表示
        keyword = None
        help_result = get_query_help(keyword)
        
        if help_result["success"]:
            help_data = help_result["help"]
            print(f"\n📚 Kuzuデータベースのクエリヘルプ")
            print(f"\n{help_data['description']}")
            
            if "commands" in help_data:
                print(f"\n【基本コマンド】\n{help_data['commands']}")
            
            if "examples" in help_data:
                print(f"\n【使用例】\n{help_data['examples']}")
            
            if "design_specific" in help_data:
                print(f"\n【このシステム固有の情報】\n{help_data['design_specific']}")
        
        return {"success": True, "message": "ヘルプを表示しました"}
    
    # クエリが指定されていない場合はエラー
    if query is None:
        return {
            "success": False,
            "message": "クエリが指定されていません。使用例を見るには '--query help' と入力してください。"
        }
    
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
