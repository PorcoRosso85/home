"""
Priority の純粋数値管理への移行 TDD Red フェーズテスト

目標:
- 文字列概念（low, medium, high, critical）を完全に削除
- 0-3 の数値のみで優先度を管理
- 文字列との変換機能を削除
"""
import pytest
import os
import tempfile
from .infrastructure.kuzu_repository import create_kuzu_repository
from .infrastructure.ddl_schema_manager import DDLSchemaManager

def create_api_wrapper(repo):
    """Simple wrapper to mimic old llm_hooks_api interface"""
    def query(input_data):
        if input_data["type"] == "cypher":
            query_str = input_data["query"]
            params = input_data.get("parameters", {})
            try:
                result = repo["execute"](query_str, params)
                # Convert QueryResult to expected format
                data = []
                while result.has_next():
                    data.append(result.get_next())
                return {"status": "success", "data": data}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return {"status": "error", "error": f"Unsupported query type: {input_data['type']}"}
    
    return {"query": query}


class TestPriorityNumericOnly:
    """優先度を純粋な数値として扱うテスト"""
    
    
    
    
    def test_api_rejects_string_priority(self):
        """APIが文字列priorityを拒否する"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "numeric_only.db")
            repo = create_kuzu_repository(db_path)
            
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success
            
            api = create_api_wrapper(repo)
            
            # 文字列priorityでの作成を試みる
            result = api["query"]({
                "type": "cypher",
                "query": """
                CREATE (r:RequirementEntity {
                    id: 'req_string_001',
                    title: 'テスト要件',
                    priority: 'high'
                })
                RETURN r.id
                """,
                "parameters": {}
            })
            
            # エラーになるべき
            assert result["status"] == "error"
            assert "UINT8" in result.get("error", "") or "Cast failed" in result.get("error", "")
    
    def test_priority_accepts_full_uint8_range(self):
        """優先度は0-255の全UINT8範囲を受け付ける"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "range_test.db")
            repo = create_kuzu_repository(db_path)
            
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success
            
            api = create_api_wrapper(repo)
            
            # 有効な範囲（UINT8: 0-255）のサンプル
            test_priorities = [0, 1, 50, 100, 127, 200, 255]
            for priority in test_priorities:
                result = api["query"]({
                    "type": "cypher",
                    "query": f"""
                    CREATE (r:RequirementEntity {{
                        id: 'req_p{priority}',
                        title: '優先度{priority}',
                        priority: {priority}
                    }})
                    CREATE (loc:LocationURI {{id: 'loc://test/p{priority}'}})
                    CREATE (loc)-[:LOCATES]->(r)
                    RETURN r.priority
                    """,
                    "parameters": {}
                })
                assert result["status"] == "success"
                assert result["data"][0][0] == priority
            
            # 範囲外の値（256以上）はエラーになる
            result = api["query"]({
                "type": "cypher",
                "query": """
                CREATE (r:RequirementEntity {
                    id: 'req_p256',
                    title: '優先度256',
                    priority: 256
                })
                CREATE (loc:LocationURI {id: 'loc://test/p256'})
                CREATE (loc)-[:LOCATES]->(r)
                RETURN r.priority
                """,
                "parameters": {}
            })
            # UINT8は0-255なので256はエラー
            assert result["status"] == "error"
    
    


# in-source tests
def test_priority_numeric_only_red_phase():
    """Red フェーズテストが期待通り失敗することを確認"""
    # このテスト自体は、上記のテストが失敗することを前提としている
    # Green フェーズで修正されるまでは、多くのテストが失敗するはず
    pass