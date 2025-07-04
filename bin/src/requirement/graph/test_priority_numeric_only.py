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


class TestPriorityNumericOnly:
    """優先度を純粋な数値として扱うテスト"""
    
    def test_priority_mapper_does_not_exist(self):
        """priority_mapper.py が存在しないことを確認"""
        mapper_path = os.path.join(
            os.path.dirname(__file__), 
            "application", 
            "priority_mapper.py"
        )
        assert not os.path.exists(mapper_path), "priority_mapper.py should not exist"
    
    def test_no_string_priority_in_schema(self):
        """スキーマコメントに文字列概念が含まれていない"""
        schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
        with open(schema_path, 'r') as f:
            content = f.read()
        
        # 文字列概念への言及がないことを確認（単語境界を考慮）
        import re
        # 優先度を表す文字列が単独の単語として現れないことを確認
        assert not re.search(r'\blow\b', content.lower())
        assert not re.search(r'\bmedium\b', content.lower())
        assert not re.search(r'\bhigh\b', content.lower())
        assert not re.search(r'\bcritical\b', content.lower())
    
    def test_api_v2_does_not_exist(self):
        """後方互換性API (llm_hooks_api_v2.py) が存在しない"""
        api_v2_path = os.path.join(
            os.path.dirname(__file__), 
            "infrastructure", 
            "llm_hooks_api_v2.py"
        )
        assert not os.path.exists(api_v2_path), "llm_hooks_api_v2.py should not exist"
    
    def test_api_rejects_string_priority(self):
        """APIが文字列priorityを拒否する"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "numeric_only.db")
            repo = create_kuzu_repository(db_path)
            
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success
            
            api = create_llm_hooks_api(repo)
            
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
            
            api = create_llm_hooks_api(repo)
            
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
    
    def test_friction_detector_uses_numeric_only(self):
        """摩擦検出が数値のみを使用"""
        from .application.friction_detector import create_friction_detector
        
        # ソースコードに文字列概念が含まれていないことを確認
        detector_path = os.path.join(
            os.path.dirname(__file__), 
            "application", 
            "friction_detector.py"
        )
        with open(detector_path, 'r') as f:
            content = f.read()
        
        # コメントとクエリに文字列概念が含まれていない
        # （変数名やメソッド名は除く）
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'critical' in line.lower():
                # critical_countのような変数名は許可
                if "'critical'" in line or '"critical"' in line:
                    pytest.fail(f"Line {i+1}: String concept 'critical' found in quotes")
    
    def test_scoring_definitions_numeric_only(self):
        """スコアリング定義が数値のみを使用"""
        # ソースファイルを直接確認
        scoring_path = os.path.join(
            os.path.dirname(__file__), 
            "application", 
            "scoring_service.py"
        )
        with open(scoring_path, 'r') as f:
            content = f.read()
        
        # メッセージ内に文字列概念が含まれていないことを確認
        # "message": "...critical..." のようなパターンを検出
        import re
        message_pattern = r'"message":\s*"([^"]+)"'
        messages = re.findall(message_pattern, content)
        
        for message in messages:
            # メッセージに文字列概念が含まれていない
            assert "critical" not in message
            assert "high" not in message or "優先度3" in message  # 優先度3への言及は許可
            assert "medium" not in message
            assert "low" not in message


# in-source tests
def test_priority_numeric_only_red_phase():
    """Red フェーズテストが期待通り失敗することを確認"""
    # このテスト自体は、上記のテストが失敗することを前提としている
    # Green フェーズで修正されるまでは、多くのテストが失敗するはず
    pass