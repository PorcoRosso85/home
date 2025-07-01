"""
KuzuDB Migration Framework
ALTER TABLE機能を活用したシンプルなマイグレーション管理
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import logging


class MigrationError(Exception):
    """マイグレーション関連のエラー"""
    pass


class KuzuMigration:
    """KuzuDBのマイグレーション管理クラス（ALTER TABLE対応）"""
    
    def __init__(self, db_path: str, migrations_dir: str = "migrations"):
        self.db_path = db_path
        self.migrations_dir = Path(migrations_dir)
        self.db = None
        self.conn = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        """データベースに接続"""
        import kuzu
        self.db = kuzu.Database(self.db_path)
        self.conn = kuzu.Connection(self.db)
        self.logger.info(f"Connected to database: {self.db_path}")
        
    def disconnect(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()
        if self.db:
            self.db.close()
        self.logger.info("Disconnected from database")
            
    def init_migration_tracking(self):
        """マイグレーション追跡用のテーブルを作成"""
        try:
            # シンプルなマイグレーション履歴テーブル
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS _migration_history (
                    id STRING,
                    name STRING,
                    applied_at TIMESTAMP,
                    checksum STRING,
                    status STRING,
                    PRIMARY KEY (id)
                )
            """)
            self.logger.info("Migration tracking table initialized")
        except Exception as e:
            raise MigrationError(f"Failed to create migration history table: {e}")
    
    def get_applied_migrations(self) -> List[Dict]:
        """適用済みのマイグレーションを取得"""
        try:
            result = self.conn.execute("""
                MATCH (m:_migration_history)
                WHERE m.status = 'completed'
                RETURN m.id as id, m.name as name, m.applied_at as applied_at, m.checksum as checksum
                ORDER BY m.applied_at
            """)
            return [dict(row) for row in result]
        except:
            return []
    
    def parse_migration_file(self, filepath: Path) -> Dict[str, any]:
        """マイグレーションファイルをパース"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # JSON形式のマイグレーション定義
        if filepath.suffix == '.json':
            return json.loads(content)
        
        # SQL/Cypher形式の場合（後方互換性）
        migration = {
            'id': filepath.stem,
            'name': filepath.name,
            'operations': []
        }
        
        # 従来の-- UP/-- DOWN形式をサポート
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
        
        if up_section:
            up_script = '\n'.join(up_section).strip()
            for statement in up_script.split(';'):
                if statement.strip():
                    migration['operations'].append(statement.strip())
                
        return migration
    
    def apply_alter_table_operation(self, operation: Dict) -> None:
        """ALTER TABLE操作を実行"""
        op_type = operation.get('type')
        table = operation.get('table')
        
        if op_type == 'add_column':
            column = operation.get('column')
            data_type = operation.get('data_type')
            default = operation.get('default')
            
            query = f"ALTER TABLE {table} ADD {column} {data_type}"
            if default is not None:
                query += f" DEFAULT {self._format_default_value(default, data_type)}"
            
            self.conn.execute(query)
            self.logger.info(f"Added column {column} to table {table}")
            
        elif op_type == 'drop_column':
            column = operation.get('column')
            if_exists = operation.get('if_exists', False)
            
            query = f"ALTER TABLE {table} DROP {'IF EXISTS ' if if_exists else ''}{column}"
            self.conn.execute(query)
            self.logger.info(f"Dropped column {column} from table {table}")
            
        elif op_type == 'rename_table':
            new_name = operation.get('new_name')
            
            query = f"ALTER TABLE {table} RENAME TO {new_name}"
            self.conn.execute(query)
            self.logger.info(f"Renamed table {table} to {new_name}")
            
        elif op_type == 'rename_column':
            old_column = operation.get('old_column')
            new_column = operation.get('new_column')
            
            query = f"ALTER TABLE {table} RENAME {old_column} TO {new_column}"
            self.conn.execute(query)
            self.logger.info(f"Renamed column {old_column} to {new_column} in table {table}")
            
        elif op_type == 'add_comment':
            comment = operation.get('comment')
            
            query = f"COMMENT ON TABLE {table} IS '{comment}'"
            self.conn.execute(query)
            self.logger.info(f"Added comment to table {table}")
            
        else:
            # その他の操作（CREATE TABLE、インデックスなど）
            query = operation.get('query')
            if query:
                self.conn.execute(query)
                self.logger.info(f"Executed custom query for {op_type}")
    
    def _format_default_value(self, value: any, data_type: str) -> str:
        """デフォルト値を適切にフォーマット"""
        if value is None:
            return "NULL"
        elif data_type in ["STRING", "VARCHAR"]:
            return f"'{value}'"
        elif data_type in ["DATE", "TIMESTAMP"]:
            return f"'{value}'"
        else:
            return str(value)
    
    def apply_migration(self, migration_data: Union[Dict, Path]) -> None:
        """マイグレーションを適用"""
        # ファイルパスが渡された場合はパース
        if isinstance(migration_data, Path):
            migration_data = self.parse_migration_file(migration_data)
            
        migration_id = migration_data['id']
        migration_name = migration_data.get('name', migration_id)
        
        # 既に適用済みかチェック
        applied = self.get_applied_migrations()
        if any(m['id'] == migration_id for m in applied):
            self.logger.info(f"Migration {migration_id} already applied, skipping...")
            return
            
        # マイグレーション開始を記録
        self.conn.execute("""
            CREATE (m:_migration_history {
                id: $id,
                name: $name,
                applied_at: timestamp(),
                status: 'in_progress'
            })
        """, {"id": migration_id, "name": migration_name})
        
        try:
            # 操作を順次実行
            operations = migration_data.get('operations', [])
            for i, operation in enumerate(operations):
                self.logger.info(f"Executing operation {i+1}/{len(operations)}")
                
                if isinstance(operation, dict):
                    self.apply_alter_table_operation(operation)
                elif isinstance(operation, str):
                    self.conn.execute(operation)
                    
            # チェックサムを計算
            checksum = hashlib.sha256(
                json.dumps(migration_data, sort_keys=True).encode()
            ).hexdigest()
            
            # マイグレーション完了を記録
            self.conn.execute("""
                MATCH (m:_migration_history {id: $id})
                SET m.status = 'completed', m.checksum = $checksum
            """, {"id": migration_id, "checksum": checksum})
            
            self.logger.info(f"Completed migration: {migration_name}")
            
        except Exception as e:
            # エラー時はステータスを更新
            self.conn.execute("""
                MATCH (m:_migration_history {id: $id})
                SET m.status = 'failed', m.error = $error
            """, {"id": migration_id, "error": str(e)})
            
            raise MigrationError(f"Failed to apply migration {migration_name}: {e}")
    
    def rollback_migration(self, migration_id: str) -> None:
        """マイグレーションをロールバック"""
        # 注意: ALTER TABLEの一部の操作は不可逆
        # 例: DROP COLUMNはデータが失われるため、ロールバック不可
        self.logger.warning(
            "Rollback capability is limited. Some operations like DROP COLUMN "
            "cannot be reversed as data is permanently lost."
        )
        
        # ロールバック用のマイグレーションファイルを探す
        rollback_file = self.migrations_dir / f"{migration_id}_rollback.json"
        if rollback_file.exists():
            rollback_data = self.parse_migration_file(rollback_file)
            self.apply_migration(rollback_data)
        else:
            raise MigrationError(
                f"No rollback file found for migration {migration_id}. "
                "Manual intervention may be required."
            )
    
    def run_migrations(self) -> None:
        """保留中のマイグレーションをすべて実行"""
        if not self.migrations_dir.exists():
            self.logger.warning(f"Migrations directory {self.migrations_dir} not found")
            return
            
        # マイグレーションファイルを取得してソート
        migration_files = sorted(self.migrations_dir.glob("*.json"))
        migration_files.extend(sorted(self.migrations_dir.glob("*.cypher")))
        migration_files.extend(sorted(self.migrations_dir.glob("*.sql")))
        
        # _rollbackファイルは除外
        migration_files = [f for f in migration_files if "_rollback" not in f.name]
        
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
            self.logger.info(f"Backup created at: {export_path}")
            return str(export_path)
        except Exception as e:
            raise MigrationError(f"Failed to create backup: {e}")


class MigrationBuilder:
    """マイグレーションファイルを作成するヘルパークラス"""
    
    @staticmethod
    def create_add_column_migration(
        table: str,
        column: str,
        data_type: str,
        default: Optional[any] = None,
        description: Optional[str] = None
    ) -> Dict:
        """ADD COLUMN マイグレーションを作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_id = f"{timestamp}_add_{column}_to_{table}"
        
        operation = {
            "type": "add_column",
            "table": table,
            "column": column,
            "data_type": data_type
        }
        
        if default is not None:
            operation["default"] = default
            
        return {
            "id": migration_id,
            "name": description or f"Add {column} to {table}",
            "operations": [operation]
        }
    
    @staticmethod
    def create_migration_file(migration_data: Dict, migrations_dir: str = "migrations") -> Path:
        """マイグレーションファイルを作成"""
        migrations_path = Path(migrations_dir)
        migrations_path.mkdir(exist_ok=True)
        
        filename = f"{migration_data['id']}.json"
        filepath = migrations_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(migration_data, f, indent=2)
            
        logging.info(f"Created migration file: {filepath}")
        return filepath
    
    @staticmethod
    def create_migration(name: str, migrations_dir: str = "migrations") -> Path:
        """新しいマイグレーションファイルを作成（後方互換性）"""
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


# 後方互換性のためのエイリアス
MigrationGenerator = MigrationBuilder


# 使用例
if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # マイグレーション作成例
    migration = MigrationBuilder.create_add_column_migration(
        table="User",
        column="email",
        data_type="STRING",
        default="",
        description="Add email field to User table"
    )
    
    print(json.dumps(migration, indent=2))
    
    # マイグレーション実行例
    # migrator = KuzuMigration("test_db", "migrations")
    # migrator.connect()
    # migrator.init_migration_tracking()
    # migrator.run_migrations()
    # migrator.disconnect()