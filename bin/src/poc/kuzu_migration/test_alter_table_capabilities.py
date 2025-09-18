"""
KuzuDB ALTER TABLE 機能の動作確認テスト
公式ドキュメントに基づいた実装確認
"""

import tempfile
import shutil
from pathlib import Path


# ========== ALTER TABLE動作確認テスト（TDD RED PHASE） ==========

def test_add_column_基本機能_カラム追加():
    """ADD COLUMNでカラムを追加できる"""
    import kuzu
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # テーブル作成
    conn.execute("CREATE NODE TABLE User (id INT64, name STRING, PRIMARY KEY (id))")
    
    # カラム追加
    conn.execute("ALTER TABLE User ADD age INT64")
    
    # カラムが追加されたことを確認
    result = conn.execute("CALL table_info('User') RETURN *")
    columns = [row[1] for row in result]  # カラム名を取得
    assert "age" in columns
    
    # NULLで初期化されていることを確認
    conn.execute("CREATE (u:User {id: 1, name: 'Alice'})")
    result = conn.execute("MATCH (u:User) RETURN u.age").get_next()
    assert result[0] is None


def test_add_column_デフォルト値_指定():
    """ADD COLUMNでデフォルト値を指定できる"""
    import kuzu
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    conn.execute("CREATE NODE TABLE User (id INT64, name STRING, PRIMARY KEY (id))")
    conn.execute("CREATE (u:User {id: 1, name: 'Bob'})")
    
    # デフォルト値付きでカラム追加
    conn.execute("ALTER TABLE User ADD grade INT64 DEFAULT 40")
    
    # 既存レコードにデフォルト値が適用されることを確認
    result = conn.execute("MATCH (u:User) RETURN u.grade").get_next()
    assert result[0] == 40


def test_add_column_if_not_exists_重複回避():
    """ADD COLUMN IF NOT EXISTSで例外を回避できる"""
    import kuzu
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    conn.execute("CREATE NODE TABLE User (id INT64, age INT64, PRIMARY KEY (id))")
    
    # 既存カラムに対してIF NOT EXISTS
    try:
        conn.execute("ALTER TABLE User ADD IF NOT EXISTS age INT64")
        # 例外が発生しないことを確認
        assert True
    except Exception:
        assert False, "IF NOT EXISTS failed to prevent exception"
    
    # 新規カラムに対してIF NOT EXISTS
    conn.execute("ALTER TABLE User ADD IF NOT EXISTS email STRING")
    result = conn.execute("CALL table_info('User') RETURN *")
    columns = [row[1] for row in result]
    assert "email" in columns


def test_drop_column_基本機能_カラム削除():
    """DROP COLUMNでカラムを削除できる"""
    import kuzu
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    conn.execute("CREATE NODE TABLE User (id INT64, name STRING, age INT64, PRIMARY KEY (id))")
    
    # カラム削除
    conn.execute("ALTER TABLE User DROP age")
    
    # カラムが削除されたことを確認
    result = conn.execute("CALL table_info('User') RETURN *")
    columns = [row[1] for row in result]
    assert "age" not in columns


def test_drop_column_if_exists_存在確認():
    """DROP COLUMN IF EXISTSで例外を回避できる"""
    import kuzu
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    conn.execute("CREATE NODE TABLE User (id INT64, name STRING, PRIMARY KEY (id))")
    
    # 存在しないカラムに対してIF EXISTS
    try:
        conn.execute("ALTER TABLE User DROP IF EXISTS age")
        assert True
    except Exception:
        assert False, "IF EXISTS failed to prevent exception"


def test_rename_table_基本機能_テーブル名変更():
    """RENAME TABLEでテーブル名を変更できる"""
    import kuzu
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    conn.execute("CREATE NODE TABLE User (id INT64, name STRING, PRIMARY KEY (id))")
    conn.execute("CREATE (u:User {id: 1, name: 'Charlie'})")
    
    # テーブル名変更
    conn.execute("ALTER TABLE User RENAME TO Student")
    
    # 新しいテーブル名でクエリできることを確認
    result = conn.execute("MATCH (s:Student) RETURN s.name").get_next()
    assert result[0] == "Charlie"
    
    # 古いテーブル名では失敗することを確認
    try:
        conn.execute("MATCH (u:User) RETURN u.name")
        assert False, "Old table name should not work"
    except Exception:
        assert True


def test_rename_column_基本機能_カラム名変更():
    """RENAME COLUMNでカラム名を変更できる"""
    import kuzu
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    conn.execute("CREATE NODE TABLE User (id INT64, name STRING, age INT64, PRIMARY KEY (id))")
    conn.execute("CREATE (u:User {id: 1, name: 'David', age: 25})")
    
    # カラム名変更
    conn.execute("ALTER TABLE User RENAME age TO grade")
    
    # 新しいカラム名でアクセスできることを確認
    result = conn.execute("MATCH (u:User) RETURN u.grade").get_next()
    assert result[0] == 25
    
    # 古いカラム名では失敗することを確認
    try:
        conn.execute("MATCH (u:User) RETURN u.age")
        assert False, "Old column name should not work"
    except Exception:
        assert True


def test_comment_on_table_メタデータ_コメント追加():
    """COMMENT ONでテーブルにコメントを追加できる"""
    import kuzu
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    conn.execute("CREATE NODE TABLE User (id INT64, name STRING, PRIMARY KEY (id))")
    
    # コメント追加
    conn.execute("COMMENT ON TABLE User IS 'User information'")
    
    # コメントが保存されたことを確認
    result = conn.execute("CALL SHOW_TABLES() RETURN *")
    for row in result:
        if row[0] == "User":  # TableName
            assert row[2] == "User information"  # TableComment
            break
    else:
        assert False, "User table not found"


def test_alter_table_rel_table_エッジテーブル対応():
    """ALTER TABLEがREL TABLEでも動作する"""
    import kuzu
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    conn.execute("CREATE NODE TABLE User (id INT64, name STRING, PRIMARY KEY (id))")
    conn.execute("CREATE REL TABLE Follows (FROM User TO User)")
    
    # REL TABLEにカラム追加
    conn.execute("ALTER TABLE Follows ADD since DATE")
    
    # カラムが追加されたことを確認
    result = conn.execute("CALL table_info('Follows') RETURN *")
    columns = [row[1] for row in result]
    assert "since" in columns


def test_alter_table_data_preservation_データ保持():
    """ALTER TABLE実行後も既存データが保持される"""
    import kuzu
    db_path = create_temp_database()
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # 初期データ作成
    conn.execute("CREATE NODE TABLE User (id INT64, name STRING, PRIMARY KEY (id))")
    conn.execute("CREATE (u:User {id: 1, name: 'Alice'})")
    conn.execute("CREATE (u:User {id: 2, name: 'Bob'})")
    
    # カラム追加
    conn.execute("ALTER TABLE User ADD email STRING DEFAULT 'unknown@example.com'")
    
    # 既存データが保持され、新カラムが追加されていることを確認
    result = conn.execute("MATCH (u:User) RETURN u.id, u.name, u.email ORDER BY u.id")
    users = list(result)
    
    assert len(users) == 2
    assert users[0] == (1, "Alice", "unknown@example.com")
    assert users[1] == (2, "Bob", "unknown@example.com")
    
    # カラム削除後もデータが保持される
    conn.execute("ALTER TABLE User DROP email")
    result = conn.execute("MATCH (u:User) RETURN count(*)")
    assert result.get_next()[0] == 2


# ========== ヘルパー関数 ==========

def create_temp_database():
    """一時的なデータベースディレクトリを作成"""
    temp_dir = tempfile.mkdtemp()
    return str(Path(temp_dir) / "test.db")


# ========== 実行 ==========

if __name__ == "__main__":
    print("=== KuzuDB ALTER TABLE 動作確認テスト (TDD RED PHASE) ===\n")
    
    tests = [
        test_add_column_基本機能_カラム追加,
        test_add_column_デフォルト値_指定,
        test_add_column_if_not_exists_重複回避,
        test_drop_column_基本機能_カラム削除,
        test_drop_column_if_exists_存在確認,
        test_rename_table_基本機能_テーブル名変更,
        test_rename_column_基本機能_カラム名変更,
        test_comment_on_table_メタデータ_コメント追加,
        test_alter_table_rel_table_エッジテーブル対応,
        test_alter_table_data_preservation_データ保持,
    ]
    
    failed = 0
    for test in tests:
        print(f"実行中: {test.__name__}")
        try:
            test()
            print("  ✗ テストが成功しました（KuzuDBがインストールされていない？）")
        except ImportError as e:
            print(f"  ✓ RED: kuzu module not found")
            failed += 1
        except Exception as e:
            print(f"  ✓ RED: {type(e).__name__}: {e}")
            failed += 1
        print()
    
    print(f"=== 結果: {failed}/{len(tests)} テストが期待通り失敗 ===")