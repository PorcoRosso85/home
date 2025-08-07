"""
Template Processor - テンプレート入力をCypherクエリに変換

最小限の実装でtemplate入力を受け付ける。
後方互換性のため、内部的にCypherクエリに変換して実行。

規約準拠:
- security.md: パラメータ化クエリによるSQLインジェクション完全防止
- layered_architecture.md: アプリケーション層からインフラ層への適切な依存
"""
from typing import Dict, Any
from requirement.graph.query import execute_query
from requirement.graph.domain.errors import NotFoundError
from requirement.graph.infrastructure.logger import debug, info, warn, error


def process_template(input_data: Dict[str, Any], repository: Dict[str, Any], search_factory=None) -> Dict[str, Any]:
    """
    テンプレート入力を処理
    
    Args:
        input_data: {"template": "...", "parameters": {...}}
        repository: KuzuDBリポジトリ
        search_factory: Search serviceを作成するファクトリー関数（オプション）
        
    Returns:
        実行結果
    """
    template = input_data.get("template", "")
    params = input_data.get("parameters", {})

    # パラメータ検証用の必須フィールド定義
    required_params = {
        "create_requirement": ["id", "title"],
        "find_requirement": ["id"],
        "add_dependency": ["from_id", "to_id"],
        "find_dependencies": ["requirement_id"],
        "update_requirement": ["id"],
        "delete_requirement": ["id"],
        "get_requirement_history": ["id"]
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

        # Search service統合を使用して重複検出（遅延初期化）
        duplicates = []
        if search_factory and search_text.strip():  # 検索テキストがある場合のみ
            search_service = search_factory()  # 必要時に初期化
            if search_service:
                try:
                    debug("rgl.template", f"Checking duplicates for: {search_text}")
                    duplicates = search_service.check_duplicates(search_text, k=5, threshold=0.5)
                    debug("rgl.template", f"Found {len(duplicates)} duplicates")
                except Exception as e:
                    error("rgl.template", f"Search service error: {e}")
                    # エラー時は重複チェックをスキップ

        # エンベディング生成
        embedding = None
        if search_factory and search_text.strip():
            search_service = search_factory() if 'search_service' not in locals() else search_service
            if search_service:
                try:
                    # SearchAdapterのgenerate_embeddingメソッドを使用
                    if hasattr(search_service, 'generate_embedding'):
                        debug("rgl.template", f"Generating embedding for: {search_text}")
                        embedding = search_service.generate_embedding(search_text)
                        if embedding:
                            debug("rgl.template", f"Generated embedding with {len(embedding)} dimensions")
                except Exception as e:
                    debug("rgl.template", f"Failed to generate embedding: {e}")
                    # エンベディング生成エラーは致命的ではない

        # 要件作成（エンベディングはVSSServiceが後から更新）
        query_params = {
            "id": params.get("id"),
            "title": params.get("title"),
            "description": params.get("description", ""),
            "status": params.get("status", "proposed")
        }

        # クエリローダーを使用して実行
        result = execute_query(repository, "create_requirement", query_params, "dml")

        # 成功時は検索インデックスに追加（重複チェックで既に初期化済みの場合のみ）
        if 'search_service' in locals() and search_service and result.get("status") == "success":
            try:
                debug("rgl.template", f"Adding to search index: {params.get('id')}")
                search_service.add_to_index({
                    "id": params.get("id"),
                    "title": params.get("title"),
                    "description": params.get("description", ""),
                    "status": params.get("status", "proposed")
                })
                debug("rgl.template", "Successfully added to search index")
            except Exception as e:
                debug("rgl.template", f"Failed to add to search index: {e}")
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
        from_id = params.get("from_id")
        to_id = params.get("to_id")
        dependency_type = params.get("dependency_type", "depends_on")
        reason = params.get("reason", "")

        # 循環依存チェック
        from requirement.graph.domain.constraints import validate_no_circular_dependency

        # 既存の依存関係を取得
        dep_result = execute_query(repository, "get_dependencies", {}, "dql")

        all_deps = {}
        if dep_result.get("status") == "success":
            for row in dep_result.get("data", []):
                dep_from_id = row[0]
                dep_to_id = row[1]
                if dep_from_id not in all_deps:
                    all_deps[dep_from_id] = []
                all_deps[dep_from_id].append(dep_to_id)

        # 新しい依存関係で循環が発生するかチェック
        validation_result = validate_no_circular_dependency(from_id, [to_id], all_deps)

        if isinstance(validation_result, dict) and validation_result.get("type") == "ConstraintViolationError":
            return {
                "error": validation_result,
                "status": "error"
            }

        # 循環がなければ依存関係を追加
        # Note: The query uses child_id/parent_id parameters
        query_params = {
            "child_id": from_id,  # Map from_id to child_id for compatibility
            "parent_id": to_id,   # Map to_id to parent_id for compatibility
            "dependency_type": dependency_type,
            "reason": reason
        }
        return execute_query(repository, "add_dependency_template", query_params, "dml")

    elif template == "find_dependencies":
        # 依存関係検索
        query_params = {
            "id": params.get("requirement_id")
        }
        # Use simple version for KuzuDB compatibility (ignores depth parameter)
        return execute_query(repository, "find_dependencies_simple", query_params, "dql")

    elif template == "update_requirement":
        # Append-Only設計: 新しいバージョンを作成
        req_id = params.get("id")
        
        # 既存の要件を取得して最新状態を確認
        existing = execute_query(repository, "find_requirement", {"id": req_id}, "dql")
        if existing.get("status") != "success" or not existing.get("data"):
            return {
                "error": {
                    "type": "NotFoundError",
                    "message": f"Requirement {req_id} not found",
                    "resource_type": "requirement",
                    "resource_id": req_id
                }
            }
        
        # 既存の要件データを取得
        current_data = existing["data"][0]
        
        # バージョン番号を抽出して次のバージョンを計算
        import re
        match = re.search(r'_v(\d+)$', req_id)
        if match:
            base_id = req_id[:match.start()]
            current_version = int(match.group(1))
            new_version = current_version + 1
        else:
            base_id = req_id
            new_version = 2
        
        # 新しいバージョンのIDを生成
        new_id = f"{base_id}_v{new_version}"
        
        # 更新パラメータを既存データとマージ
        # find_requirementクエリは r.id, r.title, r.description, r.status を返す
        new_params = {
            "id": new_id,
            "title": params.get("title", current_data[1]),  # current title
            "description": params.get("description", current_data[2]),  # current description
            "status": params.get("status", current_data[3])  # current status
        }
        
        # create_requirementテンプレートを内部的に呼び出し
        input_data["template"] = "create_requirement"
        input_data["parameters"] = new_params
        
        result = process_template(input_data, repository, search_factory)
        
        # 成功時にversion_idとprevious_versionを追加
        if result.get("status") == "success":
            result["data"] = {
                "status": "success",
                "version_id": new_id,
                "previous_version": req_id
            }
        
        return result

    elif template == "delete_requirement":
        # Append-Only設計のため、削除は許可されていません
        return NotFoundError(
            type="NotFoundError",
            message="Delete operations are not supported in this Append-Only system. Requirements are immutable.",
            resource_type="template",
            resource_id=template,
            search_criteria={"template": template}
        )

    elif template == "search_requirements":
        # Semantic search for requirements
        from .templates import process_search_template
        return process_search_template(params, search_factory)

    elif template == "get_requirement_history":
        # 要件の全バージョン履歴を取得
        req_id = params.get("id")
        
        # バージョン番号を除いたベースIDを抽出
        import re
        match = re.search(r'(.+?)(?:_v\d+)?$', req_id)
        base_id = match.group(1) if match else req_id
        
        # 全バージョンを取得
        result = execute_query(repository, "get_requirement_versions", {"base_id": base_id}, "dql")
        
        if result.get("status") == "success":
            versions = result.get("data", [])
            
            # 履歴データとして整形
            history_data = {
                "requirement_id": base_id,
                "current_version": f"v{len(versions)}" if versions else "v0",
                "total_versions": len(versions),
                "history": []
            }
            
            # 各バージョンの情報を履歴に追加
            for i, version_data in enumerate(versions):
                # バージョン番号を抽出
                version_id = version_data[0]
                if version_id == base_id:
                    version_num = 1
                else:
                    match = re.search(r'_v(\d+)$', version_id)
                    version_num = int(match.group(1)) if match else i + 1
                
                version_info = {
                    "version": f"v{version_num}",
                    "version_id": version_data[0],      # version_id
                    "title": version_data[1],           # title
                    "description": version_data[2],     # description
                    "status": version_data[3],          # status
                    "operation": "CREATE" if version_num == 1 else "UPDATE"
                }
                
                # 変更点を特定（前バージョンとの比較）
                if i > 0:
                    prev = versions[i-1]
                    changes = []
                    if prev[1] != version_data[1]:  # title
                        changes.append("title")
                    if prev[2] != version_data[2]:  # description
                        changes.append("description")
                    if prev[3] != version_data[3]:  # status
                        changes.append("status")
                    version_info["changes"] = changes
                
                history_data["history"].append(version_info)
            
            return {
                "status": "success",
                "data": history_data
            }
        
        return result

    else:
        return NotFoundError(
            type="NotFoundError",
            message=f"Unknown template: {template}",
            resource_type="template",
            resource_id=template,
            search_criteria={"template": template}
        )
