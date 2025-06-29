"""
Priority Recalculation Module
優先順位再計算モジュール

このモジュールは、要件の優先順位を管理し、衝突を解決するための
アプリケーション層実装を提供します。

使用例:
    >>> import kuzu
    >>> from priority_manager import PriorityManager
    >>> 
    >>> # データベース接続
    >>> db = kuzu.Database(":memory:")
    >>> conn = kuzu.Connection(db)
    >>> 
    >>> # スキーマ作成
    >>> conn.execute('''
    ...     CREATE NODE TABLE RequirementEntity (
    ...         id STRING PRIMARY KEY,
    ...         title STRING,
    ...         priority UINT8 DEFAULT 128
    ...     )
    ... ''')
    >>> 
    >>> # マネージャー初期化
    >>> manager = PriorityManager(conn)
    >>> 
    >>> # 優先順位の再配分
    >>> manager.redistribute_priorities()
    >>> 
    >>> # 最優先の競合解決
    >>> manager.handle_max_priority_conflict('req_urgent')

主要機能:
    - redistribute_priorities: 0-255範囲で均等再配分
    - compress_priorities: 既存優先順位を圧縮
    - normalize_priorities: 指定範囲に正規化
    - handle_max_priority_conflict: 最優先競合の解決
    - auto_cascade_priorities: 自動カスケード
    - batch_insert_with_redistribution: バッチ挿入と再配分

エクスポート:
    PriorityManager: 優先順位管理クラス
"""

from priority_manager import PriorityManager

__all__ = ['PriorityManager']

# 実行可能な使用例
def example_basic_usage():
    """基本的な使用例"""
    import kuzu
    
    # セットアップ
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            priority UINT8 DEFAULT 128
        )
    """)
    
    # テストデータ
    requirements = [
        ("REQ-001", "認証機能", 50),
        ("REQ-002", "データベース接続", 100),
        ("REQ-003", "API実装", 150),
    ]
    
    for id, title, priority in requirements:
        conn.execute(f"""
            CREATE (:RequirementEntity {{
                id: '{id}',
                title: '{title}',
                priority: {priority}
            }})
        """)
    
    # マネージャー使用
    manager = PriorityManager(conn)
    
    # 再配分実行
    result = manager.redistribute_priorities()
    print(f"再配分完了: {len(result)}件")
    
    # 結果確認
    query_result = conn.execute("""
        MATCH (r:RequirementEntity)
        RETURN r.id, r.priority
        ORDER BY r.priority
    """)
    
    print("\n再配分後の優先順位:")
    while query_result.has_next():
        row = query_result.get_next()
        print(f"  {row[0]}: {row[1]}")


def example_conflict_resolution():
    """最優先競合の解決例"""
    import kuzu
    
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # スキーマとデータ作成
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            priority UINT8
        )
    """)
    
    # 既存の最優先タスク
    conn.execute("""
        CREATE (:RequirementEntity {
            id: 'REQ-001',
            title: '既存の最優先',
            priority: 255
        })
    """)
    
    # 新しい最優先タスク追加
    conn.execute("""
        CREATE (:RequirementEntity {
            id: 'REQ-URGENT',
            title: '緊急対応',
            priority: 255
        })
    """)
    
    manager = PriorityManager(conn)
    
    # 競合解決
    manager.handle_max_priority_conflict('REQ-URGENT')
    
    # 結果確認
    result = conn.execute("""
        MATCH (r:RequirementEntity)
        RETURN r.id, r.title, r.priority
        ORDER BY r.priority DESC
    """)
    
    print("\n競合解決後:")
    while result.has_next():
        row = result.get_next()
        print(f"  {row[0]}: {row[1]} (優先度: {row[2]})")


# in-sourceテスト（規約準拠）
def test_priority_manager_基本機能_正常動作():
    """PriorityManagerの基本機能テスト"""
    import kuzu
    
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            priority UINT8
        )
    """)
    
    conn.execute("CREATE (:RequirementEntity {id: 'R1', priority: 10})")
    conn.execute("CREATE (:RequirementEntity {id: 'R2', priority: 20})")
    
    manager = PriorityManager(conn)
    result = manager.redistribute_priorities()
    
    assert len(result) == 2
    assert result[0]['new_priority'] == 0
    assert result[1]['new_priority'] == 255


def test_priority_compression_圧縮率50_正常圧縮():
    """優先順位圧縮のテスト"""
    import kuzu
    
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            priority UINT8
        )
    """)
    
    conn.execute("CREATE (:RequirementEntity {id: 'R1', priority: 100})")
    
    manager = PriorityManager(conn)
    result = manager.compress_priorities(0.5)
    
    assert len(result) == 1
    assert result[0]['compressed_priority'] == 50


if __name__ == "__main__":
    print("=== 基本使用例 ===")
    example_basic_usage()
    
    print("\n=== 競合解決例 ===")
    example_conflict_resolution()
    
    print("\n=== テスト実行 ===")
    test_priority_manager_基本機能_正常動作()
    print("✓ 基本機能テスト: PASS")
    
    test_priority_compression_圧縮率50_正常圧縮()
    print("✓ 圧縮機能テスト: PASS")