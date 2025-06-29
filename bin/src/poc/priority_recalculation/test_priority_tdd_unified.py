"""
Priority Recalculation TDD Unified Tests
統合TDDテスト - Red→Green progression + 異常系
"""
import kuzu
import tempfile
import shutil
import pytest
from pathlib import Path
from priority_manager import PriorityManager


class TestPriorityTDDProgression:
    """TDD Red→Green progression tests"""
    
    @pytest.fixture
    def db_path(self):
        """Create temporary database directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def conn(self, db_path):
        """Create database connection with schema"""
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        
        conn.execute("""
            CREATE NODE TABLE RequirementEntity (
                id STRING PRIMARY KEY,
                title STRING,
                description STRING,
                priority UINT8 DEFAULT 128
            )
        """)
        
        # Insert test data
        test_data = [
            ("req_001", "First requirement", "Description 1", 10),
            ("req_002", "Second requirement", "Description 2", 50),
            ("req_003", "Third requirement", "Description 3", 100),
            ("req_004", "Fourth requirement", "Description 4", 150),
            ("req_005", "Fifth requirement", "Description 5", 200),
        ]
        
        for id, title, desc, priority in test_data:
            conn.execute(f"""
                CREATE (:RequirementEntity {{
                    id: '{id}',
                    title: '{title}',
                    description: '{desc}',
                    priority: {priority}
                }})
            """)
        
        yield conn
        conn.close()
    
    # ========== Red→Green: 優先順位再配分 ==========
    def test_redistribute_priorities_red_then_green(self, conn):
        """RED: 実装なし → GREEN: PriorityManagerで実装"""
        # RED Phase: 実装前（このコメントは実装後も残す）
        # 最初はPriorityManagerクラスが存在しなかった
        # with pytest.raises(NameError):
        #     manager = PriorityManager(conn)
        
        # GREEN Phase: 実装後
        manager = PriorityManager(conn)
        result = manager.redistribute_priorities()
        
        # 期待値: 均等配分 [0, 63, 127, 191, 255]
        assert len(result) == 5
        expected = [0, 63, 127, 191, 255]
        for i, req in enumerate(result):
            assert req['new_priority'] == expected[i]
    
    # ========== Red→Green: 優先順位圧縮 ==========
    def test_compress_priorities_red_then_green(self, conn):
        """RED: 実装なし → GREEN: compress_prioritiesメソッド実装"""
        # RED Phase: 最初はメソッドが存在しなかった
        # manager = PriorityManager(conn)
        # with pytest.raises(AttributeError):
        #     manager.compress_priorities(0.5)
        
        # GREEN Phase: 実装後
        manager = PriorityManager(conn)
        result = manager.compress_priorities(0.5)
        
        # 期待値: 各値が0.5倍
        expected_compressions = {
            'req_001': 5,   # 10 * 0.5
            'req_002': 25,  # 50 * 0.5
            'req_003': 50,  # 100 * 0.5
        }
        
        for item in result:
            if item['id'] in expected_compressions:
                assert item['compressed_priority'] == expected_compressions[item['id']]
    
    # ========== Red→Green: 最大優先度競合 ==========
    def test_max_priority_conflict_red_then_green(self, conn):
        """RED: 競合未解決 → GREEN: handle_max_priority_conflict実装"""
        # 既存の最大優先度を設定
        conn.execute("""
            MATCH (r:RequirementEntity {id: 'req_005'})
            SET r.priority = 255
        """)
        
        # 新しい最大優先度を追加
        conn.execute("""
            CREATE (:RequirementEntity {
                id: 'req_urgent',
                title: 'Super urgent',
                priority: 255
            })
        """)
        
        # RED Phase: 競合が存在（両方255）
        result = conn.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.priority = 255
            RETURN count(r) AS conflict_count
        """)
        assert result.get_next()[0] == 2  # 競合あり
        
        # GREEN Phase: 競合解決
        manager = PriorityManager(conn)
        manager.handle_max_priority_conflict('req_urgent')
        
        # 期待値: req_urgentが255、req_005は降格
        result = conn.execute("""
            MATCH (r:RequirementEntity {id: 'req_urgent'})
            RETURN r.priority
        """)
        assert result.get_next()[0] == 255
        
        result = conn.execute("""
            MATCH (r:RequirementEntity {id: 'req_005'})
            RETURN r.priority
        """)
        assert result.get_next()[0] < 255


class TestPriorityErrorCases:
    """異常系テスト"""
    
    @pytest.fixture
    def conn(self):
        """Create in-memory database"""
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        
        conn.execute("""
            CREATE NODE TABLE RequirementEntity (
                id STRING PRIMARY KEY,
                title STRING,
                priority UINT8 DEFAULT 128
            )
        """)
        
        yield conn
        conn.close()
    
    @pytest.fixture
    def manager(self, conn):
        return PriorityManager(conn)
    
    # ========== 異常系: 圧縮率エラー ==========
    def test_compress_priorities_無効な圧縮率_エラー(self, conn, manager):
        """圧縮率が範囲外の場合"""
        # ケース1: 圧縮率が0以下
        with pytest.raises(ValueError) as exc_info:
            manager.compress_priorities(0)
        assert "Compression factor must be between 0 and 1" in str(exc_info.value)
        
        # ケース2: 圧縮率が1以上
        with pytest.raises(ValueError) as exc_info:
            manager.compress_priorities(1.5)
        assert "Compression factor must be between 0 and 1" in str(exc_info.value)
    
    # ========== 異常系: 空のデータベース ==========
    def test_redistribute_priorities_空DB_空リスト返却(self, conn, manager):
        """データが無い場合の処理"""
        result = manager.redistribute_priorities()
        assert result == []
    
    # ========== 異常系: 優先順位オーバーフロー ==========
    def test_priority_overflow_255超過_エラー(self, conn, manager):
        """優先順位が255を超える場合"""
        # 255の要件を作成
        for i in range(10):
            conn.execute(f"""
                CREATE (:RequirementEntity {{
                    id: 'req_max_{i}',
                    priority: 255
                }})
            """)
        
        # さらに追加しようとする
        conn.execute("""
            CREATE (:RequirementEntity {
                id: 'req_overflow',
                priority: 255
            })
        """)
        
        # 解決を試みる
        manager.handle_max_priority_conflict('req_overflow')
        
        # 全ての優先順位が0-255の範囲内であることを確認
        result = conn.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.priority < 0 OR r.priority > 255
            RETURN count(r) AS out_of_range
        """)
        assert result.get_next()[0] == 0
    
    # ========== 異常系: トランザクションロールバック ==========
    def test_transaction_rollback_エラー時_変更なし(self, conn, manager):
        """エラー時にロールバックされることを確認"""
        # 初期データ追加
        conn.execute("""
            CREATE (:RequirementEntity {
                id: 'req_test',
                priority: 100
            })
        """)
        
        # redistribute_prioritiesを改造してエラーを発生させる
        # （実際のテストでは、モックやパッチを使用）
        original_execute = conn.execute
        
        def failing_execute(query):
            if "SET r.priority" in query:
                raise Exception("Simulated database error")
            return original_execute(query)
        
        conn.execute = failing_execute
        
        # エラーが発生することを確認
        with pytest.raises(Exception):
            manager.redistribute_priorities()
        
        # 元に戻す
        conn.execute = original_execute
        
        # 優先順位が変更されていないことを確認
        result = conn.execute("""
            MATCH (r:RequirementEntity {id: 'req_test'})
            RETURN r.priority
        """)
        assert result.get_next()[0] == 100  # 元の値のまま
    
    # ========== 異常系: 無効なID ==========
    def test_handle_conflict_存在しないID_エラーなし(self, conn, manager):
        """存在しないIDで競合解決を試みる"""
        # 存在しないIDで実行（エラーは出ないが、何も起きない）
        manager.handle_max_priority_conflict('non_existent_id')
        
        # データベースに影響がないことを確認
        result = conn.execute("""
            MATCH (r:RequirementEntity)
            RETURN count(r)
        """)
        assert result.get_next()[0] == 0
    
    # ========== 異常系: 同一優先順位の大量データ ==========
    def test_all_same_priority_正規化_中間値設定(self, conn, manager):
        """全て同じ優先順位の場合"""
        # 全て同じ優先順位で作成
        for i in range(5):
            conn.execute(f"""
                CREATE (:RequirementEntity {{
                    id: 'req_same_{i}',
                    priority: 100
                }})
            """)
        
        # 正規化実行
        result = manager.normalize_priorities(0, 255)
        
        # 全て中間値（127）になることを確認
        db_result = conn.execute("""
            MATCH (r:RequirementEntity)
            RETURN r.priority
        """)
        
        priorities = []
        while db_result.has_next():
            priorities.append(db_result.get_next()[0])
        
        assert all(p == 127 for p in priorities)  # 全て中間値
    
    # ========== 異常系: バッチ挿入の部分失敗 ==========
    def test_batch_insert_部分失敗_全体ロールバック(self, conn, manager):
        """バッチ挿入で一部が失敗する場合"""
        # 不正なデータを含むバッチ
        new_requirements = [
            {'id': 'req_valid_1', 'title': 'Valid 1', 'priority': 50},
            {'id': None, 'title': 'Invalid', 'priority': 100},  # 無効なID
            {'id': 'req_valid_2', 'title': 'Valid 2', 'priority': 150},
        ]
        
        # エラーが発生することを確認
        with pytest.raises(Exception):
            manager.batch_insert_with_redistribution(new_requirements)
        
        # 何も挿入されていないことを確認（ロールバック）
        result = conn.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.id IN ['req_valid_1', 'req_valid_2']
            RETURN count(r)
        """)
        assert result.get_next()[0] == 0


class TestPriorityDataTypeValidation:
    """UINT8データ型検証テスト"""
    
    @pytest.fixture
    def conn(self):
        """Create in-memory database with UINT8 priority"""
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        
        conn.execute("""
            CREATE NODE TABLE RequirementEntity (
                id STRING PRIMARY KEY,
                title STRING,
                priority UINT8 DEFAULT 128
            )
        """)
        
        yield conn
        conn.close()
    
    # ========== Red→Green: 文字列挿入エラー ==========
    def test_priority_string_insertion_red_then_green(self, conn):
        """RED: 文字列を挿入しようとする → GREEN: 型エラーで保護される"""
        
        # RED Phase: 文字列を優先順位に設定しようとする
        with pytest.raises(RuntimeError) as exc_info:
            conn.execute("""
                CREATE (:RequirementEntity {
                    id: 'req_string',
                    title: 'String priority test',
                    priority: 'high'
                })
            """)
        
        # GREEN Phase: KuzuDBが型エラーを返す
        assert "expected UINT8" in str(exc_info.value) or "data type STRING" in str(exc_info.value)
        
        # データが挿入されていないことを確認
        result = conn.execute("""
            MATCH (r:RequirementEntity)
            RETURN count(r)
        """)
        assert result.get_next()[0] == 0
    
    # ========== 異常系: 様々な不正な型 ==========
    def test_priority_invalid_types_全てエラー(self, conn):
        """様々な不正な型の挿入を試みる"""
        
        invalid_values = [
            ('high', '文字列'),
            ('255.5', '小数文字列'),
            ('true', 'ブール文字列'),
            ('[1,2,3]', '配列文字列'),
            ('null', 'null文字列'),
            ('', '空文字列'),
            ('２５５', '全角数字'),
        ]
        
        for value, description in invalid_values:
            with pytest.raises(RuntimeError) as exc_info:
                conn.execute(f"""
                    CREATE (:RequirementEntity {{
                        id: 'req_invalid_{value}',
                        title: '{description}',
                        priority: '{value}'
                    }})
                """)
            
            # エラーメッセージに型関連の内容が含まれることを確認
            error_msg = str(exc_info.value)
            assert any(keyword in error_msg for keyword in ["Cannot cast", "Expected", "type", "UINT8"])
    
    # ========== Green: 有効な数値 ==========
    def test_priority_valid_numbers_正常挿入(self, conn):
        """有効な数値は正常に挿入される"""
        
        valid_values = [
            (0, '最小値'),
            (1, '1'),
            (127, 'INT8最大値'),
            (128, 'UINT8中間値'),
            (255, 'UINT8最大値'),
        ]
        
        for value, description in valid_values:
            conn.execute(f"""
                CREATE (:RequirementEntity {{
                    id: 'req_valid_{value}',
                    title: '{description}',
                    priority: {value}
                }})
            """)
        
        # 全て正常に挿入されたことを確認
        result = conn.execute("""
            MATCH (r:RequirementEntity)
            RETURN count(r)
        """)
        assert result.get_next()[0] == len(valid_values)
    
    # ========== 異常系: 範囲外の数値 ==========
    def test_priority_out_of_range_エラー(self, conn):
        """UINT8の範囲外の数値"""
        
        out_of_range_values = [
            (-1, '負の値'),
            (-128, 'INT8最小値'),
            (256, 'UINT8最大値+1'),
            (1000, '大きすぎる値'),
        ]
        
        for value, description in out_of_range_values:
            with pytest.raises(RuntimeError) as exc_info:
                conn.execute(f"""
                    CREATE (:RequirementEntity {{
                        id: 'req_outrange_{abs(value)}',
                        title: '{description}',
                        priority: {value}
                    }})
                """)
            
            # オーバーフローエラーを確認
            assert "overflow" in str(exc_info.value).lower() or "out of range" in str(exc_info.value).lower()
    
    # ========== 異常系: パラメータ化クエリでの型保護 ==========
    def test_priority_parameterized_query_型保護(self, conn):
        """パラメータ化クエリでも型が保護される"""
        
        # 文字列パラメータを渡す
        with pytest.raises(RuntimeError):
            conn.execute("""
                CREATE (:RequirementEntity {
                    id: $id,
                    title: $title,
                    priority: $priority
                })
            """, {"id": "req_param", "title": "Param test", "priority": "high"})
        
        # 範囲外の数値パラメータ
        with pytest.raises(RuntimeError):
            conn.execute("""
                CREATE (:RequirementEntity {
                    id: $id,
                    title: $title,
                    priority: $priority
                })
            """, {"id": "req_param2", "title": "Param test 2", "priority": 300})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])