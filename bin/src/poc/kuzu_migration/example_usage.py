"""
KuzuDB Migration Framework 使用例
"""

from migration_framework import KuzuMigration, MigrationGenerator
from pathlib import Path


def example_create_migrations():
    """マイグレーションファイルの作成例"""
    
    # 1. ユーザーテーブルの作成
    MigrationGenerator.create_migration("create_users_table")
    
    # 2. プロダクトテーブルの作成
    MigrationGenerator.create_migration("create_products_table")
    
    # 3. ユーザーテーブルにemailカラムを追加
    MigrationGenerator.create_migration("add_email_to_users")


def example_migration_content():
    """マイグレーションファイルの内容例"""
    
    # migrations/20240115_100000_create_users_table.cypher
    create_users = """-- Migration: create_users_table
-- Created at: 2024-01-15 10:00:00

-- UP
CREATE NODE TABLE users (
    id INT64,
    name STRING,
    created_at TIMESTAMP,
    PRIMARY KEY (id)
);

-- DOWN
DROP TABLE users;
"""
    
    # migrations/20240115_110000_add_email_to_users.cypher
    add_email = """-- Migration: add_email_to_users
-- Created at: 2024-01-15 11:00:00

-- UP
-- KuzuDBでは直接的なALTER TABLEが限定的なため、
-- 新しいテーブルを作成してデータを移行する
CREATE NODE TABLE users_new (
    id INT64,
    name STRING,
    email STRING,
    created_at TIMESTAMP,
    PRIMARY KEY (id)
);

-- 既存データを移行
MATCH (u:users)
CREATE (un:users_new {
    id: u.id,
    name: u.name,
    email: '',
    created_at: u.created_at
});

-- 古いテーブルを削除
DROP TABLE users;

-- DOWN
-- 元の構造に戻す
CREATE NODE TABLE users (
    id INT64,
    name STRING,
    created_at TIMESTAMP,
    PRIMARY KEY (id)
);

MATCH (un:users_new)
CREATE (u:users {
    id: un.id,
    name: un.name,
    created_at: un.created_at
});

DROP TABLE users_new;
"""
    
    return create_users, add_email


def example_run_migrations():
    """マイグレーションの実行例"""
    
    # データベースパスとマイグレーションディレクトリを指定
    db_path = "example_db"
    migrations_dir = "migrations"
    
    # マイグレーションインスタンスを作成
    migration = KuzuMigration(db_path, migrations_dir)
    
    try:
        # データベースに接続
        migration.connect()
        
        # マイグレーション追跡テーブルを初期化
        migration.init_migration_tracking()
        
        # すべての保留中のマイグレーションを実行
        print("Running migrations...")
        migration.run_migrations()
        
        # 適用済みマイグレーションを確認
        applied = migration.get_applied_migrations()
        print(f"\nApplied migrations: {len(applied)}")
        for m in applied:
            print(f"- {m['name']} (applied at: {m['applied_at']})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        migration.disconnect()


def example_rollback():
    """マイグレーションのロールバック例"""
    
    migration = KuzuMigration("example_db", "migrations")
    
    try:
        migration.connect()
        
        # 最新のマイグレーションをロールバック
        applied = migration.get_applied_migrations()
        if applied:
            latest = applied[-1]
            print(f"Rolling back: {latest['name']}")
            migration.rollback_migration(latest['id'])
            
    finally:
        migration.disconnect()


def example_backup_restore():
    """バックアップとリストアの例"""
    
    migration = KuzuMigration("example_db", "migrations")
    
    try:
        migration.connect()
        
        # バックアップを作成
        print("Creating backup...")
        backup_path = migration.create_backup()
        print(f"Backup created: {backup_path}")
        
        # リストアする場合は、新しい空のデータベースで
        # IMPORT DATABASE コマンドを実行
        
    finally:
        migration.disconnect()


def example_schema_diff():
    """スキーマの差分検出例（概念的な実装）"""
    
    def get_schema(conn):
        """現在のスキーマを取得"""
        tables = {}
        
        # ノードテーブルを取得
        result = conn.execute("CALL table_info() RETURN *;")
        for row in result:
            table_name = row[0]
            table_type = row[1]
            if table_type == "NODE":
                # テーブルの詳細情報を取得
                schema_result = conn.execute(f"CALL show_node_table('{table_name}') RETURN *;")
                tables[table_name] = {
                    "type": "NODE",
                    "properties": list(schema_result)
                }
                
        return tables
    
    # スキーマの比較ロジックを実装
    # ...


if __name__ == "__main__":
    print("KuzuDB Migration Framework Examples")
    print("=" * 50)
    
    # マイグレーションファイルを作成
    # example_create_migrations()
    
    # マイグレーションを実行
    # example_run_migrations()
    
    # ロールバック
    # example_rollback()
    
    # バックアップ
    # example_backup_restore()