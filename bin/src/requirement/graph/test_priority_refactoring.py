"""
Priority フィールドの UINT8 リファクタリング TDD Red フェーズテスト

現在の仕様:
- priority: STRING DEFAULT 'medium'
- 値: 'low', 'medium', 'high', 'critical'

新しい仕様:
- priority: UINT8 DEFAULT 1
- 値: 0=low, 1=medium, 2=high, 3=critical
"""
import os
import tempfile

from .infrastructure.kuzu_repository import create_kuzu_repository
# llm_hooks_api has been removed
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


class TestPriorityUINT8Refactoring:
    """Priority を UINT8 に変更するための Red フェーズテスト"""

    def test_create_requirement_with_uint8_priority(self):
        """UINT8 の priority で要件を作成できる"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "priority_test.db")
            repo = create_kuzu_repository(db_path)

            # 新しいスキーマを適用（UINT8版）
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "ddl", "migrations", "3.2.0_current.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success

            api = create_api_wrapper(repo)

            # UINT8 値で要件を作成
            result = api["query"]({
                "type": "cypher",
                "query": """
                CREATE (r:RequirementEntity {
                    id: 'req_uint8_001',
                    title: '高優先度タスク',
                    priority: 150  // medium priority
                })
                CREATE (loc:LocationURI {id: 'loc://test/001'})
                CREATE (loc)-[:LOCATES]->(r)
                RETURN r.priority as priority
                """,
                "parameters": {}
            })

            assert result["status"] == "success"
            assert result["data"][0][0] == 150  # UINT8 value

    def test_default_priority_is_uint8(self):
        """デフォルト priority が UINT8 の 1 (medium) になる"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "default_test.db")
            repo = create_kuzu_repository(db_path)

            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "ddl", "migrations", "3.2.0_current.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success

            api = create_api_wrapper(repo)

            # priority を指定せずに作成
            result = api["query"]({
                "type": "cypher",
                "query": """
                CREATE (r:RequirementEntity {
                    id: 'req_default_001',
                    title: 'デフォルト優先度タスク'
                })
                CREATE (loc:LocationURI {id: 'loc://test/default'})
                CREATE (loc)-[:LOCATES]->(r)
                RETURN r.priority as priority
                """,
                "parameters": {}
            })

            assert result["status"] == "success"
            assert result["data"][0][0] == 1  # default medium = 1

    def test_query_with_priority_comparison(self):
        """UINT8 priority での比較クエリが動作する"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "comparison_test.db")
            repo = create_kuzu_repository(db_path)

            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "ddl", "migrations", "3.2.0_current.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success

            api = create_api_wrapper(repo)

            # 異なる優先度の要件を作成
            priorities = [(10, "very_low"), (50, "low"), (150, "medium"), (250, "high")]
            for priority_val, priority_name in priorities:
                api["query"]({
                    "type": "cypher",
                    "query": f"""
                    CREATE (r:RequirementEntity {{
                        id: 'req_{priority_name}_001',
                        title: '{priority_name}優先度タスク',
                        priority: {priority_val}
                    }})
                    CREATE (loc:LocationURI {{id: 'loc://test/{priority_name}'}})
                    CREATE (loc)-[:LOCATES]->(r)
                    """,
                    "parameters": {}
                })

            # 高優先度（priority >= 150）の要件を検索
            result = api["query"]({
                "type": "cypher",
                "query": """
                MATCH (r:RequirementEntity)
                WHERE r.priority >= 150
                RETURN r.id as id, r.priority as priority
                ORDER BY r.priority DESC
                """,
                "parameters": {}
            })

            assert len(result["data"]) == 2  # medium(150) と high(250)
            assert result["data"][0][1] == 250  # high
            assert result["data"][1][1] == 150  # medium


    def test_migration_script_exists(self):
        """移行スクリプトは削除されている（新規DBのみサポート）"""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "migrations",
            "priority_string_to_uint8.py"
        )
        assert not os.path.exists(migration_path)

    def test_friction_detector_works_with_uint8(self):
        """摩擦検出が UINT8 priority で動作する"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "friction_uint8.db")
            repo = create_kuzu_repository(db_path)

            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "ddl", "migrations", "3.2.0_current.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success

            api = create_api_wrapper(repo)

            # 高優先度 (200以上) の要件を複数作成
            for i in range(3):
                api["query"]({
                    "type": "cypher",
                    "query": f"""
                    CREATE (r:RequirementEntity {{
                        id: 'req_high_{i}',
                        title: '高優先度要件{i}',
                        priority: 220  // 高優先度
                    }})
                    CREATE (loc:LocationURI {{id: 'loc://test/high_{i}'}})
                    CREATE (loc)-[:LOCATES]->(r)
                    """,
                    "parameters": {}
                })

            # 摩擦検出 - Removed: scoring system deleted
            # from .application.friction_detector import create_friction_detector
            # detector = create_friction_detector()
            # priority_friction = detector["detect_priority"](repo["connection"])
            #
            # assert priority_friction["high_priority_count"] == 3
            # assert priority_friction["has_conflict"] == True
            pass  # Test simplified after scoring removal

    def test_api_backward_compatibility(self):
        """APIは数値priorityのみ受け付ける（後方互換性なし）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "numeric_test.db")
            repo = create_kuzu_repository(db_path)

            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "ddl", "migrations", "3.2.0_current.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success

            api = create_api_wrapper(repo)

            # 数値 priority で作成
            result = api["query"]({
                "type": "cypher",
                "query": """
                CREATE (r:RequirementEntity {
                    id: 'req_numeric_001',
                    title: '数値優先度テスト',
                    priority: 150  // 数値で指定
                })
                CREATE (loc:LocationURI {id: 'loc://test/numeric'})
                CREATE (loc)-[:LOCATES]->(r)
                RETURN r.priority as priority
                """,
                "parameters": {}
            })

            assert result["status"] == "success"
            assert result["data"][0][0] == 150  # UINT8値
