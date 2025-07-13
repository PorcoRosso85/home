"""
Template Processor - テンプレート入力をCypherクエリに変換

最小限の実装でtemplate入力を受け付ける。
後方互換性のため、内部的にCypherクエリに変換して実行。
"""
from typing import Dict, Any, Optional
from .poc_search_adapter import POCSearchAdapter


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
        query = """
        CREATE (r:RequirementEntity {
            id: $id,
            title: $title,
            description: $description,
            status: $status,
            embedding: NULL
        })
        RETURN r
        """
        query_params = {
            "id": params.get("id"),
            "title": params.get("title"),
            "description": params.get("description", ""),
            "status": params.get("status", "proposed")
        }
        
        # クエリ実行
        result = repository["execute"](query, query_params)
        
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
                print(f"[DEBUG] Successfully added to search index")
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
        query = "MATCH (r:RequirementEntity {id: $id}) RETURN r"
        query_params = {"id": params.get("id")}
        
    elif template == "list_requirements":
        # 要件一覧
        limit = params.get("limit", 100)
        query = f"MATCH (r:RequirementEntity) RETURN r LIMIT {limit}"
        query_params = {}
        
    elif template == "add_dependency":
        # 依存関係追加の前に循環検証
        child_id = params.get("child_id")
        parent_id = params.get("parent_id")
        
        # 循環依存チェック
        from ..domain.constraints import validate_no_circular_dependency
        
        # 既存の依存関係を取得
        dep_query = """
        MATCH (r:RequirementEntity)-[:DEPENDS_ON]->(dep:RequirementEntity)
        RETURN r.id as from_id, dep.id as to_id
        """
        dep_result = repository["execute"](dep_query, {})
        
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
        query = """
        MATCH (child:RequirementEntity {id: $child_id})
        MATCH (parent:RequirementEntity {id: $parent_id})
        CREATE (child)-[:DEPENDS_ON]->(parent)
        RETURN child, parent
        """
        query_params = {
            "child_id": child_id,
            "parent_id": parent_id
        }
        
    elif template == "find_dependencies":
        # 依存関係検索
        depth = params.get("depth", 1)
        query = f"""
        MATCH path = (r:RequirementEntity {{id: $id}})-[:DEPENDS_ON*1..{depth}]->(dep:RequirementEntity)
        RETURN dep, length(path) as distance
        ORDER BY distance
        """
        query_params = {"id": params.get("requirement_id")}
        
    elif template == "update_requirement":
        # 要件更新
        updates = []
        query_params = {"id": params.get("id")}
        
        if "title" in params:
            updates.append("r.title = $title")
            query_params["title"] = params["title"]
        if "description" in params:
            updates.append("r.description = $description")
            query_params["description"] = params["description"]
        if "status" in params:
            updates.append("r.status = $status")
            query_params["status"] = params["status"]
            
        if updates:
            query = f"MATCH (r:RequirementEntity {{id: $id}}) SET {', '.join(updates)} RETURN r"
        else:
            return {"error": {"type": "ValidationError", "message": "No fields to update"}}
            
    elif template == "delete_requirement":
        # 要件削除
        query = "MATCH (r:RequirementEntity {id: $id}) DETACH DELETE r"
        query_params = {"id": params.get("id")}
        
    else:
        return {
            "error": {
                "type": "TemplateNotFoundError",
                "message": f"Unknown template: {template}"
            }
        }
    
    # Cypherクエリを実行
    return repository["execute"](query, query_params)