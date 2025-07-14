"""
Template Processor - テンプレート入力をCypherクエリに変換

最小限の実装でtemplate入力を受け付ける。
後方互換性のため、内部的にCypherクエリに変換して実行。

規約準拠:
- security.md: パラメータ化クエリによるSQLインジェクション完全防止
- layered_architecture.md: アプリケーション層からインフラ層への適切な依存
"""
from typing import Dict, Any, Optional
from .poc_search_adapter import POCSearchAdapter
from ..query import execute_query


def process_template(input_data: Dict[str, Any], repository: Dict[str, Any], poc_search: Optional[POCSearchAdapter] = None) -> Dict[str, Any]:
    """
    テンプレート入力を処理
    
    Args:
        input_data: {"template": "...", "parameters": {...}}
        repository: KuzuDBリポジトリ
        search_integration: POC search統合（オプション）
        
    Returns:
        実行結果
    """
    print(f"[DEBUG] process_template called with poc_search={poc_search}")
    template = input_data.get("template", "")
    params = input_data.get("parameters", {})

    # パラメータ検証用の必須フィールド定義
    required_params = {
        "create_requirement": ["id", "title"],
        "find_requirement": ["id"],
        "add_dependency": ["child_id", "parent_id"],
        "find_dependencies": ["requirement_id"],
        "update_requirement": ["id"],
        "delete_requirement": ["id"]
    }

    # 必須パラメータチェック
    if template in required_params:
        missing = [p for p in required_params[template] if not params.get(p)]
        if missing:
            return {
                "error": {
                    "type": "MissingParameterError",
                    "message": f"Missing required parameters: {', '.join(missing)}",
                    "template": template,
                    "required": required_params[template]
                }
            }

    # テンプレート→Cypherマッピング（最小限の実装）
    if template == "create_requirement":
        # 要件作成前に重複チェック
        duplicates = []
        # タイトルと説明を組み合わせて検索
        search_text = f"{params.get('title', '')} {params.get('description', '')}"

        # POC search統合を使用して重複検出
        duplicates = []
        if poc_search:
            try:
                print(f"[DEBUG] Checking duplicates for: {search_text}")
                duplicates = poc_search.check_duplicates(search_text, k=5, threshold=0.5)
                print(f"[DEBUG] Found {len(duplicates)} duplicates")
            except Exception as e:
                print(f"POC search error: {e}")
                # エラー時は重複チェックをスキップ

        # 要件作成（embeddingはNULLで作成）
        query_params = {
            "id": params.get("id"),
            "title": params.get("title"),
            "description": params.get("description", ""),
            "status": params.get("status", "proposed")
        }

        # クエリローダーを使用して実行
        result = execute_query(repository, "create_requirement", query_params, "dml")

        # 成功時は検索インデックスに追加
        if poc_search and result.get("status") == "success":
            try:
                print(f"[DEBUG] Adding to search index: {params.get('id')}")
                poc_search.add_to_index({
                    "id": params.get("id"),
                    "title": params.get("title"),
                    "description": params.get("description", ""),
                    "status": params.get("status", "proposed")
                })
                print("[DEBUG] Successfully added to search index")
            except Exception as e:
                print(f"[DEBUG] Failed to add to search index: {e}")
                # インデックス追加エラーは致命的ではない

        # 重複警告を結果に含める
        if duplicates and result.get("status") == "success":
            result["warning"] = {
                "type": "DuplicateWarning",
                "message": "Similar requirements found",
                "duplicates": duplicates
            }

        return result

    elif template == "find_requirement":
        # 要件検索
        query_params = {"id": params.get("id")}
        return execute_query(repository, "find_requirement", query_params, "dql")

    elif template == "list_requirements":
        # 要件一覧
        query_params = {"limit": params.get("limit", 100)}
        return execute_query(repository, "list_requirements", query_params, "dql")

    elif template == "add_dependency":
        # 依存関係追加の前に循環検証
        child_id = params.get("child_id")
        parent_id = params.get("parent_id")

        # 循環依存チェック
        from ..domain.constraints import validate_no_circular_dependency

        # 既存の依存関係を取得
        dep_result = execute_query(repository, "get_dependencies", {}, "dql")

        all_deps = {}
        if dep_result.get("status") == "success":
            for row in dep_result.get("data", []):
                from_id = row[0]
                to_id = row[1]
                if from_id not in all_deps:
                    all_deps[from_id] = []
                all_deps[from_id].append(to_id)

        # 新しい依存関係で循環が発生するかチェック
        validation_result = validate_no_circular_dependency(child_id, [parent_id], all_deps)

        if isinstance(validation_result, dict) and validation_result.get("type") == "ConstraintViolationError":
            return {
                "error": validation_result,
                "status": "error"
            }

        # 循環がなければ依存関係を追加
        query_params = {
            "child_id": child_id,
            "parent_id": parent_id
        }
        return execute_query(repository, "add_dependency", query_params, "dml")

    elif template == "find_dependencies":
        # 依存関係検索
        query_params = {
            "id": params.get("requirement_id"),
            "depth": params.get("depth", 1)
        }
        return execute_query(repository, "find_dependencies", query_params, "dql")

    elif template == "update_requirement":
        # 要件更新
        query_params = {"id": params.get("id")}
        updates = {}

        if "title" in params:
            updates["title"] = params["title"]
        if "description" in params:
            updates["description"] = params["description"]
        if "status" in params:
            updates["status"] = params["status"]

        if updates:
            query_params["updates"] = updates
            return execute_query(repository, "update_requirement", query_params, "dml")
        else:
            return {"error": {"type": "ValidationError", "message": "No fields to update"}}

    elif template == "delete_requirement":
        # 要件削除
        query_params = {"id": params.get("id")}
        return execute_query(repository, "delete_requirement", query_params, "dml")

    else:
        return {
            "error": {
                "type": "TemplateNotFoundError",
                "message": f"Unknown template: {template}"
            }
        }
