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
    
    # connectionが提供されていればそれを使用
    if "connection" in repository:
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
                if proc_name == "requirement.score":
                    score = procedures.score_requirement_similarity(args[0], args[1], args[2])
                    return {"status": "success", "data": {"score": score}}
                    
                elif proc_name == "requirement.progress":
                    progress = procedures.calculate_requirement_progress(args[0])
                    return {"status": "success", "data": progress}
                    
                elif proc_name == "graph.validate":
                    issues = procedures.validate_graph_constraints()
                    return {"status": "success", "data": {"issues": issues}}
                    
                else:
                    return {
                        "status": "error",
                        "error": f"Unknown procedure: {proc_name}",
                        "available_procedures": [
                            "requirement.score",
                            "requirement.progress",
                            "graph.validate"
                        ]
                    }
                    
            else:
                return {
                    "status": "error",
                    "error": f"Unknown query type: {query_type}",
                    "supported_types": ["cypher", "template", "procedure"]
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


# Test cases
def test_llm_hooks_api_template_query_正常実行():
    """create_llm_hooks_api_テンプレートクエリ_正常に実行"""
    # テスト用のモックリポジトリ
    def create_test_repository():
        test_results = []
        
        def test_execute(query, params=None):
            # 簡易的な結果を返す
            class Result:
                def __init__(self):
                    self.rows = []
                    self.metadata = {"row_count": 0}
            return Result()
        
        class TestConnection:
            def execute(self, query, params=None):
                return test_execute(query, params)
        
        class TestDB:
            def connect(self):
                return TestConnection()
        
        return {
            "db": TestDB(),
            "executor": {
                "execute": lambda q, p: {"rows": [], "metadata": {"row_count": 0}}
            }
        }
    
    repo = create_test_repository()
    api = create_llm_hooks_api(repo)
    
    result = api["query"]({
        "type": "template",
        "template": "find_requirement",
        "parameters": {"req_id": "req_001"}
    })
    
    assert result["status"] == "success"
    assert "data" in result


def test_llm_hooks_api_batch_query_複数実行():
    """create_llm_hooks_api_バッチクエリ_複数結果を返す"""
    # テスト用のモックリポジトリ
    def create_test_repository():
        class TestConnection:
            def execute(self, query, params=None):
                class Result:
                    def __init__(self):
                        self.rows = []
                        self.metadata = {"row_count": 0}
                return Result()
        
        class TestDB:
            def connect(self):
                return TestConnection()
        
        return {
            "db": TestDB(),
            "executor": {
                "execute": lambda q, p: {"rows": [], "metadata": {"row_count": 0}}
            }
        }
    
    repo = create_test_repository()
    api = create_llm_hooks_api(repo)
    
    requests = [
        {"type": "template", "template": "find_requirement", "parameters": {"req_id": "req_001"}},
        {"type": "template", "template": "find_dependencies", "parameters": {"req_id": "req_001"}}
    ]
    
    results = api["batch_query"](requests)
    
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)


def test_llm_hooks_api_cypher_query_検証あり_実行():
    """create_llm_hooks_api_Cypherクエリ_検証後に実行"""
    # テスト用モックリポジトリ
    def create_test_repository():
        class TestValidator:
            def validate_query(self, query):
                return {"is_valid": True, "errors": []}
        
        return {
            "db": type('TestDB', (), {'connect': lambda self: None})(),
            "executor": {
                "execute": lambda q, p: {"rows": [{"id": "req_001"}], "metadata": {"row_count": 1}}
            },
            "validator": TestValidator()
        }
    
    repo = create_test_repository()
    api = create_llm_hooks_api(repo)
    
    result = api["query"]({
        "type": "cypher",
        "query": "MATCH (r:RequirementEntity) RETURN r",
        "parameters": {}
    })
    
    assert result["status"] == "success"
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "req_001"


def test_llm_hooks_api_procedure_call_スコア計算():
    """create_llm_hooks_api_プロシージャ_スコアを返す"""
    # テスト用モックリポジトリ
    def create_test_repository():
        class TestProcedures:
            def score_requirement_similarity(self, req_id, query, method):
                return 0.85
            
            def calculate_requirement_progress(self, req_id):
                return 0.75
            
            def validate_graph_constraints(self):
                return []
        
        class TestConnection:
            pass
        
        return {
            "db": type('TestDB', (), {'connect': lambda self: TestConnection()})(),
            "connection": TestConnection(),
            "procedures": TestProcedures()
        }
    
    repo = create_test_repository()
    api = create_llm_hooks_api(repo)
    
    result = api["query"]({
        "type": "procedure",
        "procedure": "requirement.score",
        "args": ["req_001", "test query", "similarity"]
    })
    
    assert result["status"] == "success"
    assert result["data"]["score"] == 0.85


def test_llm_hooks_api_suggest_action_要件なし_全体提案():
    """suggest_next_action_要件ID無し_全体的な提案を返す"""
    # テスト用モックリポジトリ
    def create_test_repository():
        return {
            "db": type('TestDB', (), {'connect': lambda self: None})(),
            "executor": {
                "execute": lambda q, p: {"rows": [], "metadata": {"row_count": 0}}
            }
        }
    
    repo = create_test_repository()
    api = create_llm_hooks_api(repo)
    
    suggestions = api["suggest_next_action"]()
    
    assert len(suggestions) >= 2
    assert any(s["action"] == "find_incomplete" for s in suggestions)
    assert any(s["action"] == "check_circular_dependencies" for s in suggestions)
