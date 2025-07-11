"""DDLスキーマ管理モジュールのテスト"""

import tempfile
import os
import sys
from .ddl_schema_manager import DDLSchemaManager

# テストでのみ使用するインポート（実行時のみ）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


class TestDDLSchemaManager:
    """DDLSchemaManagerのテスト"""

    def test_parse_cypher_statements_コメント除去_正しくパース(self):
        """_parse_cypher_statements_コメントあり_コメントが除去される"""
        # Arrange
        manager = DDLSchemaManager(None)
        content = """
        // This is a comment
        CREATE NODE TABLE Test (
            id STRING PRIMARY KEY
        );

        /* Block comment */
        CREATE REL TABLE TestRel (
            FROM Test TO Test
        );
        """

        # Act
        statements = manager._parse_cypher_statements(content)

        # Assert
        assert len(statements) == 2
        assert 'CREATE NODE TABLE Test' in statements[0]
        assert 'CREATE REL TABLE TestRel' in statements[1]
        assert '//' not in ''.join(statements)
        assert '/*' not in ''.join(statements)


    def test_handle_duplicate_rel_tables_重複テーブル_リネーム(self):
        """_handle_duplicate_rel_tables_重複REL TABLE_一意な名前に変更"""
        # Arrange
        manager = DDLSchemaManager(None)
        statements = [
            "CREATE NODE TABLE A (id STRING PRIMARY KEY);",
            "CREATE REL TABLE LOCATES (FROM LocationURI TO CodeEntity);",
            "CREATE REL TABLE LOCATES (FROM LocationURI TO RequirementEntity);",
            "CREATE REL TABLE LOCATES (FROM LocationURI TO ReferenceEntity);",
            "CREATE REL TABLE OTHER (FROM A TO B);"
        ]

        # Act
        processed = manager._handle_duplicate_rel_tables(statements)

        # Assert
        assert len(processed) == 5
        assert processed[0] == statements[0]  # NODE TABLEは変更なし
        assert "LOCATES" in processed[1]  # 最初のLOCATESは変更なし
        assert "LOCATES_LocationURI_RequirementEntity" in processed[2]  # 2番目はリネーム
        assert "LOCATES_LocationURI_ReferenceEntity" in processed[3]  # 3番目もリネーム
        assert processed[4] == statements[4]  # 他のREL TABLEは変更なし

    def test_apply_schema_正常系_スキーマ適用(self):
        """apply_schema_有効なスキーマ_正常に適用される"""
        # Arrange
        from .database_factory import create_database, create_connection

        # テスト用の簡易スキーマ
        schema_content = """
        CREATE NODE TABLE TestEntity (
            id STRING PRIMARY KEY,
            name STRING
        );

        CREATE REL TABLE TEST_REL (
            FROM TestEntity TO TestEntity
        );
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.cypher', delete=False) as f:
            f.write(schema_content)
            schema_path = f.name

        # インメモリDBを使用
        db = create_database(in_memory=True, use_cache=False, test_unique=True)
        conn = create_connection(db)
            manager = DDLSchemaManager(conn)

            try:
                # Act
                success, results = manager.apply_schema(schema_path)

                # Assert
                assert success
                assert len(results) == 2
                assert all('✓' in r for r in results)

                # 実際にテーブルが作成されたか確認
                conn.execute("CREATE (n:TestEntity {id: 'test_001', name: 'Test'})")
                result = conn.execute("MATCH (n:TestEntity) RETURN count(n) as cnt")
                assert result.has_next()
                assert result.get_next()[0] == 1

            finally:
                conn.close()
            os.unlink(schema_path)

    def test_rollback_適用済みスキーマ_ロールバック成功(self):
        """rollback_適用済みスキーマ_正常にロールバック"""
        # Arrange
        from .database_factory import create_database, create_connection

        # インメモリDBを使用
        db = create_database(in_memory=True, use_cache=False, test_unique=True)
        conn = create_connection(db)
            manager = DDLSchemaManager(conn)

            # スキーマを適用
            conn.execute("CREATE NODE TABLE TestForRollback (id STRING PRIMARY KEY)")
            manager.applied_statements.append("CREATE NODE TABLE TestForRollback (id STRING PRIMARY KEY);")

            # Act
            success, results = manager.rollback()

            # Assert
            assert success
            assert len(results) == 1
            assert 'DROP TABLE TestForRollback' in results[0]

            # テーブルが削除されたか確認（エラーが発生すればOK）
            try:
                conn.execute("CREATE (n:TestForRollback {id: 'test'})")
                raise AssertionError("Table should have been dropped")
            except:
                pass  # Expected

        conn.close()
