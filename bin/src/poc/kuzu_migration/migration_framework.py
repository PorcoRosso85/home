"""
KuzuDB Migration Framework
データベースマイグレーションを管理するためのフレームワーク
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import kuzu


class MigrationError(Exception):
    """マイグレーション関連のエラー"""
    pass


class KuzuMigration:
    """KuzuDBのマイグレーション管理クラス"""
    
    def __init__(self, db_path: str, migrations_dir: str = "migrations"):
        self.db_path = db_path
        self.migrations_dir = Path(migrations_dir)
        self.db = None
        self.conn = None
        
    def connect(self):
        """データベースに接続"""
        self.db = kuzu.Database(self.db_path)
        self.conn = kuzu.Connection(self.db)
        
    def disconnect(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()
        if self.db:
            self.db.close()
            
    def init_migration_tracking(self):
        """マイグレーション追跡用のテーブルを作成"""
        try:
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS migration_history (
                    id STRING,
                    name STRING,
                    applied_at TIMESTAMP,
                    checksum STRING,
                    PRIMARY KEY (id)
                )
            """)
        except Exception as e:
            raise MigrationError(f"Failed to create migration history table: {e}")
    
    def get_applied_migrations(self) -> List[Dict]:
        """適用済みのマイグレーションを取得"""
        try:
            result = self.conn.execute("""
                MATCH (m:migration_history)
                RETURN m.id as id, m.name as name, m.applied_at as applied_at, m.checksum as checksum
                ORDER BY m.applied_at
            """)
            return [dict(row) for row in result]
        except:
            return []
    
    def calculate_checksum(self, content: str) -> str:
        """マイグレーションファイルのチェックサムを計算"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def parse_migration_file(self, filepath: Path) -> Tuple[str, str]:
        """マイグレーションファイルをパースしてUPとDOWNセクションを抽出"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.split('\n')
        up_section = []
        down_section = []
        current_section = None
        
        for line in lines:
            if line.strip().upper() == '-- UP':
                current_section = 'up'
                continue
            elif line.strip().upper() == '-- DOWN':
                current_section = 'down'
                continue
                
            if current_section == 'up':
                up_section.append(line)
            elif current_section == 'down':
                down_section.append(line)
                
        return '\n'.join(up_section).strip(), '\n'.join(down_section).strip()
    
    def apply_migration(self, migration_file: Path):
        """マイグレーションを適用"""
        migration_id = migration_file.stem
        migration_name = migration_file.name
        
        # 既に適用済みかチェック
        applied = self.get_applied_migrations()
        if any(m['id'] == migration_id for m in applied):
            print(f"Migration {migration_id} already applied, skipping...")
            return
            
        # マイグレーションファイルを読み込み
        up_script, down_script = self.parse_migration_file(migration_file)
        checksum = self.calculate_checksum(up_script + down_script)
        
        try:
            # UPスクリプトを実行
            statements = [s.strip() for s in up_script.split(';') if s.strip()]
            for statement in statements:
                self.conn.execute(statement)
                
            # マイグレーション履歴に記録
            self.conn.execute("""
                CREATE (m:migration_history {
                    id: $id,
                    name: $name,
                    applied_at: timestamp(),
                    checksum: $checksum
                })
            """, {"id": migration_id, "name": migration_name, "checksum": checksum})
            
            print(f"Applied migration: {migration_name}")
            
        except Exception as e:
            raise MigrationError(f"Failed to apply migration {migration_name}: {e}")
    
    def rollback_migration(self, migration_id: str):
        """マイグレーションをロールバック"""
        # 適用済みマイグレーションを確認
        applied = self.get_applied_migrations()
        migration = next((m for m in applied if m['id'] == migration_id), None)
        
        if not migration:
            raise MigrationError(f"Migration {migration_id} not found in history")
            
        # マイグレーションファイルを探す
        migration_file = self.migrations_dir / f"{migration_id}.cypher"
        if not migration_file.exists():
            raise MigrationError(f"Migration file {migration_file} not found")
            
        # DOWNスクリプトを実行
        _, down_script = self.parse_migration_file(migration_file)
        
        try:
            statements = [s.strip() for s in down_script.split(';') if s.strip()]
            for statement in statements:
                self.conn.execute(statement)
                
            # マイグレーション履歴から削除
            self.conn.execute("""
                MATCH (m:migration_history {id: $id})
                DELETE m
            """, {"id": migration_id})
            
            print(f"Rolled back migration: {migration_id}")
            
        except Exception as e:
            raise MigrationError(f"Failed to rollback migration {migration_id}: {e}")
    
    def run_migrations(self):
        """保留中のマイグレーションをすべて実行"""
        if not self.migrations_dir.exists():
            print(f"Migrations directory {self.migrations_dir} not found")
            return
            
        # マイグレーションファイルを取得してソート
        migration_files = sorted(self.migrations_dir.glob("*.cypher"))
        
        for migration_file in migration_files:
            self.apply_migration(migration_file)
            
    def create_backup(self, backup_dir: str = "backups") -> str:
        """データベースのバックアップを作成"""
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = backup_path / f"kuzu_backup_{timestamp}"
        
        try:
            self.conn.execute(f"EXPORT DATABASE '{export_path}' (format='parquet')")
            print(f"Backup created at: {export_path}")
            return str(export_path)
        except Exception as e:
            raise MigrationError(f"Failed to create backup: {e}")


class MigrationGenerator:
    """マイグレーションファイルを生成するヘルパークラス"""
    
    @staticmethod
    def create_migration(name: str, migrations_dir: str = "migrations") -> Path:
        """新しいマイグレーションファイルを作成"""
        migrations_path = Path(migrations_dir)
        migrations_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.cypher"
        filepath = migrations_path / filename
        
        template = """-- Migration: {name}
-- Created at: {timestamp}

-- UP
-- Write your migration statements here


-- DOWN
-- Write your rollback statements here

"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template.format(name=name, timestamp=datetime.now()))
            
        print(f"Created migration file: {filepath}")
        return filepath


if __name__ == "__main__":
    # 使用例
    migration = KuzuMigration("test_db", "migrations")
    
    try:
        migration.connect()
        migration.init_migration_tracking()
        
        # マイグレーションを実行
        migration.run_migrations()
        
        # バックアップを作成
        # backup_path = migration.create_backup()
        
    finally:
        migration.disconnect()