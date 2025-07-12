"""
Template Processor - テンプレート入力をCypherクエリに変換

最小限の実装でtemplate入力を受け付ける。
後方互換性のため、内部的にCypherクエリに変換して実行。
"""
from typing import Dict, Any, Optional
from application.search_integration import SearchIntegration


def process_template(input_data: Dict[str, Any], repository: Dict[str, Any], search_integration: Optional[SearchIntegration] = None) -> Dict[str, Any]:
    """
    テンプレート入力を処理
    
    Args:
        input_data: {"template": "...", "parameters": {...}}
        repository: KuzuDBリポジトリ
        search_integration: POC search統合（オプション）
        
    Returns:
        実行結果
    """
    template = input_data.get("template", "")
    params = input_data.get("parameters", {})
    
    # テンプレート→Cypherマッピング（最小限の実装）
    if template == "create_requirement":
        # 要件作成前に重複チェック
        if search_integration:
            title = params.get("title", "")
            duplicates = search_integration.check_duplicates(title, k=5, threshold=0.7)
            
            if duplicates:
                return {
                    "warning": {
                        "type": "DuplicateWarning",
                        "message": "Similar requirements found",
                        "duplicates": duplicates
                    },
                    "continue": True  # 作成は継続可能
                }
        
        # 要件作成
        query = """
        CREATE (r:RequirementEntity {
            id: $id,
            title: $title,
            description: $description,
            status: $status
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
        if search_integration and result.get("status") == "success":
            requirement_data = result.get("data", [{}])[0]
            if requirement_data:
                search_integration.add_to_search_index({
                    "id": params.get("id"),
                    "title": params.get("title"),
                    "description": params.get("description", ""),
                    "status": params.get("status", "proposed")
                })
        
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
        # 依存関係追加
        query = """
        MATCH (child:RequirementEntity {id: $child_id})
        MATCH (parent:RequirementEntity {id: $parent_id})
        CREATE (child)-[:DEPENDS_ON]->(parent)
        RETURN child, parent
        """
        query_params = {
            "child_id": params.get("child_id"),
            "parent_id": params.get("parent_id")
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