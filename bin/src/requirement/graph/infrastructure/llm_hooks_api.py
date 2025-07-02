"""
LLM Hooks API - LLMが直接クエリできる統一インターフェース（関数ベース版）
依存: domain, application
外部依存: なし
"""
from typing import Dict, List, Any, Optional, Union

# 相対インポートのみ使用
from .cypher_executor import CypherExecutor
from .query_validator import QueryValidator
from .custom_procedures import CustomProcedures
from .variables import get_db_path
from .logger import debug, info, warn, error


def create_llm_hooks_api(repository: Dict) -> Dict[str, Any]:
    """
    LLMが要件グラフと対話するための統一APIを作成
    Cypherクエリとカスタムプロシージャの両方をサポート
    
    Args:
        repository: KuzuDBリポジトリ（execute, save_requirement等を持つ）
        
    Returns:
        API関数の辞書
    """
    # executorが提供されていればそれを使用、なければ新規作成
    if "executor" in repository:
        executor = repository["executor"]
    else:
        executor = CypherExecutor(repository["db"].connect())
    
    validator = QueryValidator()
    
    # proceduresが提供されていればそれを使用
    if "procedures" in repository:
        procedures = repository["procedures"]
    # connectionが提供されていればそれを使用
    elif "connection" in repository:
        procedures = CustomProcedures(repository["connection"])
    else:
        procedures = CustomProcedures(repository["db"].connect())
    
    # 許可するクエリテンプレート
    query_templates = {
        # 要件探索
        "find_requirement": """
            MATCH (r:RequirementEntity {id: $req_id})
            RETURN r
        """,
        
        "search_requirements": """
            MATCH (r:RequirementEntity)
            WHERE r.title CONTAINS $keyword OR r.description CONTAINS $keyword
            RETURN r
            LIMIT $limit
        """,
        
        # 依存関係
        "find_dependencies": """
            MATCH (r:RequirementEntity {id: $req_id})-[:DEPENDS_ON]->(dep:RequirementEntity)
            RETURN dep
        """,
        
        "find_dependents": """
            MATCH (dep:RequirementEntity)-[:DEPENDS_ON]->(r:RequirementEntity {id: $req_id})
            RETURN dep
        """,
        
        # 階層関係（LocationURI使用）
        "find_children": """
            MATCH (r:RequirementEntity {id: $req_id})
            MATCH (l:LocationURI)-[:LOCATES_LocationURI_RequirementEntity]->(r)
            MATCH (l)-[:CONTAINS_LOCATION]->(child_l:LocationURI)
            MATCH (child_l)-[:LOCATES_LocationURI_RequirementEntity]->(child:RequirementEntity)
            RETURN child
        """,
        
        "find_parent": """
            MATCH (r:RequirementEntity {id: $req_id})
            MATCH (l:LocationURI)-[:LOCATES_LocationURI_RequirementEntity]->(r)
            MATCH (parent_l:LocationURI)-[:CONTAINS_LOCATION]->(l)
            MATCH (parent_l)-[:LOCATES_LocationURI_RequirementEntity]->(parent:RequirementEntity)
            RETURN parent
            LIMIT 1
        """,
        
        # 実装状況
        "check_implementation": """
            MATCH (r:RequirementEntity {id: $req_id})
            OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
            RETURN r, collect(c) as implementations
        """,
        
        # 進捗集計（全体）
        "calculate_progress": """
            MATCH (r:RequirementEntity)
            WITH count(r) as total,
                 count(CASE WHEN r.status = 'completed' THEN 1 END) as completed
            RETURN total, completed, 
                   CASE WHEN total > 0 THEN completed * 1.0 / total ELSE 0 END as progress
        """
    }
    
    def query(request: Dict[str, Any]) -> Dict[str, Any]:
        """
        統一クエリインターフェース
        
        Args:
            request: クエリリクエスト
                - type: "cypher" | "template" | "procedure"
                - query/template/procedure: 実行内容
                - parameters/args: パラメータ
                
        Returns:
            実行結果
        """
        query_type = request.get("type", "cypher")
        
        try:
            if query_type == "cypher":
                # 直接Cypherクエリ（検証付き）
                query_str = request.get("query", "")
                params = request.get("parameters", {})
                
                # クエリ検証
                is_valid, error = validator.validate(query_str)
                if not is_valid:
                    return {
                        "status": "error",
                        "error": "Query validation failed",
                        "details": error
                    }
                
                # 実行
                result = executor.execute(query_str, params)
                if "error" in result:
                    return {
                        "status": "error",
                        "error": result["error"]["message"],
                        "type": result["error"]["type"]
                    }
                return {
                    "status": "success",
                    "data": result.get("data", []),
                    "metadata": {
                        "row_count": result.get("row_count", 0),
                        "columns": result.get("columns", [])
                    }
                }
                
            elif query_type == "batch":
                # バッチクエリ
                queries = request.get("queries", [])
                results = []
                for q in queries:
                    results.append(query(q))
                return {
                    "status": "success",
                    "results": results
                }
                
            elif query_type == "template":
                # テンプレートクエリ
                template_name = request.get("template", "")
                params = request.get("parameters", {})
                
                if template_name not in query_templates:
                    return {
                        "status": "error",
                        "error": f"Unknown template: {template_name}",
                        "available_templates": list(query_templates.keys())
                    }
                
                query_str = query_templates[template_name]
                result = executor.execute(query_str, params)
                if "error" in result:
                    return {
                        "status": "error",
                        "error": result["error"]["message"],
                        "type": result["error"]["type"]
                    }
                return {
                    "status": "success",
                    "data": result.get("data", []),
                    "metadata": {
                        "row_count": result.get("row_count", 0),
                        "columns": result.get("columns", [])
                    }
                }
                
            elif query_type == "procedure":
                # カスタムプロシージャ
                proc_name = request.get("procedure", "")
                args = request.get("args", [])
                
                # プロシージャ実行
                if proc_name == "requirement.similar":
                    similar = procedures.find_similar_requirements(args[0], args[1])
                    return {"status": "success", "data": {"similar_requirements": similar}}
                    
                elif proc_name == "requirement.progress":
                    progress = procedures.calculate_requirement_progress(args[0])
                    return {"status": "success", "data": progress}
                    
                elif proc_name == "graph.validate":
                    issues = procedures.validate_graph_constraints()
                    return {"status": "success", "data": {"issues": issues}}
                    
                elif proc_name == "requirement.score":
                    # スコア計算プロシージャ
                    if hasattr(procedures, 'score_requirement_similarity'):
                        score = procedures.score_requirement_similarity(args[0], args[1], args[2] if len(args) > 2 else "similarity")
                        return {"status": "success", "data": {"score": score}}
                    else:
                        return {"status": "error", "error": "Score procedure not implemented"}
                    
                else:
                    return {
                        "status": "error",
                        "error": f"Unknown procedure: {proc_name}",
                        "available_procedures": [
                            "requirement.similar",
                            "requirement.progress",
                            "graph.validate"
                        ]
                    }
                    
            else:
                return {
                    "status": "error",
                    "error": f"Unknown query type: {query_type}",
                    "supported_types": ["cypher", "template", "procedure", "batch"]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "type": e.__class__.__name__
            }
    
    def batch_query(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        バッチクエリ実行
        
        Args:
            requests: クエリリクエストのリスト
            
        Returns:
            実行結果のリスト
        """
        results = []
        for request in requests:
            results.append(query(request))
        return results
    
    def suggest_next_action(current_req_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        次のアクションを提案
        
        Args:
            current_req_id: 現在の要件ID（オプション）
            
        Returns:
            提案リスト
        """
        suggestions = []
        
        if not current_req_id:
            # 全体的な提案
            suggestions.append({
                "action": "find_incomplete",
                "description": "Find incomplete requirements",
                "query": """
                    MATCH (r:RequirementEntity)
                    WHERE r.status <> 'completed'
                    RETURN r
                    ORDER BY r.priority DESC
                    LIMIT 5
                """
            })
            
            suggestions.append({
                "action": "check_circular_dependencies",
                "description": "Check for circular dependencies",
                "procedure": "graph.validate"
            })
            
        else:
            # 特定要件に基づく提案
            # 依存関係の確認
            dep_result = executor.execute(
                "MATCH (r:RequirementEntity {id: $req_id})-[:DEPENDS_ON]->(dep) RETURN count(dep) as dep_count",
                {"req_id": current_req_id}
            )
            
            if not dep_result.get("error") and dep_result.get("data") and len(dep_result["data"]) > 0 and dep_result["data"][0][0] > 0:
                suggestions.append({
                    "action": "check_dependencies",
                    "description": "Check if dependencies are completed",
                    "query": f"""
                        MATCH (r:RequirementEntity {{id: '{current_req_id}'}})-[:DEPENDS_ON]->(dep:RequirementEntity)
                        WHERE dep.status <> 'completed'
                        RETURN dep
                    """
                })
            
            # 実装状況の確認
            suggestions.append({
                "action": "check_implementation",
                "description": "Check implementation status",
                "template": "check_implementation",
                "parameters": {"req_id": current_req_id}
            })
            
            # 子要件の進捗確認
            progress = procedures.calculate_requirement_progress(current_req_id)
            if progress < 1.0:
                suggestions.append({
                    "action": "work_on_children",
                    "description": f"Complete child requirements (progress: {progress:.1%})",
                    "query": f"""
                        MATCH (r:RequirementEntity {{id: '{current_req_id}'}})
                        MATCH (l:LocationURI)-[:LOCATES_LocationURI_RequirementEntity]->(r)
                        MATCH (l)-[:CONTAINS_LOCATION]->(child_l:LocationURI)
                        MATCH (child_l)-[:LOCATES_LocationURI_RequirementEntity]->(child:RequirementEntity)
                        WHERE child.status <> 'completed'
                        RETURN child
                        LIMIT 1
                    """
                })
        
        return suggestions
    
    return {
        "query": query,
        "batch_query": batch_query,
        "suggest_next_action": suggest_next_action,
        "templates": query_templates,
        "executor": executor,
        "validator": validator,
        "procedures": procedures
    }
