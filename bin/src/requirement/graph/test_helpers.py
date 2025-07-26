"""
テストヘルパー関数 - サブプロセスを使わない高速テスト実行
"""
import os
import sys
import json
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 直接インポート
from requirement.graph.infrastructure.database_factory import create_database, create_connection
from requirement.graph.infrastructure.ddl_schema_manager import DDLSchemaManager
from requirement.graph.application.template_processor import process_template
from requirement.graph.domain.errors import DatabaseError


class FastTestRunner:
    """高速テスト実行のためのランナー"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or ":memory:"
        self._db = None
        self._conn = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """初期化を確実に行う"""
        if self._initialized:
            return
            
        # データベース作成
        self._db = create_database(
            path=self.db_path,
            in_memory=self.db_path.startswith(":memory:"),
            test_unique=True
        )
        
        if isinstance(self._db, dict) and self._db.get("type") == "DatabaseError":
            raise RuntimeError(f"Database creation failed: {self._db.get('message', 'Unknown error')}")
            
        # 接続作成
        self._conn = create_connection(self._db)
        if isinstance(self._conn, dict) and self._conn.get("type") == "DatabaseError":
            raise RuntimeError(f"Connection creation failed: {self._conn.get('message', 'Unknown error')}")
            
        # スキーマ適用 - 最新のマイグレーションファイルを使用
        schema_manager = DDLSchemaManager(self._conn)
        migration_path = Path(__file__).parent / "ddl" / "migrations" / "3.4.0_search_integration.cypher"
        success, messages = schema_manager.apply_schema(str(migration_path))
        if not success:
            raise RuntimeError(f"Schema application failed: {messages}")
        
        # テンプレートプロセッサーは関数として使用
        
        self._initialized = True
        
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """システムの公開APIをエミュレート"""
        self._ensure_initialized()
        
        try:
            request_type = input_data.get("type")
            
            if request_type == "schema":
                action = input_data.get("action")
                if action == "apply":
                    # すでに初期化時に適用済み
                    return {"status": "success", "message": "Schema already applied"}
                    
            elif request_type == "template":
                template_name = input_data.get("template")
                parameters = input_data.get("parameters", {})
                
                # リポジトリを作成して使用
                from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository
                repository = create_kuzu_repository(self.db_path)
                
                # テンプレート実行
                result = process_template(
                    {"template": template_name, "parameters": parameters},
                    repository
                )
                
                if hasattr(result, "__dict__"):
                    # エラーオブジェクトの場合
                    return {"error": str(result)}
                    
                return {"data": result}
                
            elif request_type == "query":
                query = input_data.get("query")
                parameters = input_data.get("parameters", {})
                
                # 直接クエリ実行
                result = self._conn.execute(query, parameters)
                rows = []
                while result.has_next():
                    rows.append(result.get_next())
                    
                return {"data": rows}
                
            else:
                return {"error": f"Unknown request type: {request_type}"}
                
        except Exception as e:
            return {"error": str(e)}
            
    def cleanup(self):
        """リソースのクリーンアップ"""
        if self._conn:
            self._conn.close()
            

def create_fast_test_environment():
    """高速テスト環境のファクトリー関数"""
    return FastTestRunner()


def run_system_fast(input_data: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    既存のrun_system関数の高速版
    サブプロセスの代わりに直接実行する
    """
    runner = FastTestRunner(db_path)
    try:
        return runner.run(input_data)
    finally:
        runner.cleanup()


# 既存のテストとの互換性のために、環境変数でモードを切り替え
if os.environ.get("RGL_FAST_TEST_MODE", "true").lower() == "true":
    # 高速モードを有効化（デフォルト）
    run_system = run_system_fast
else:
    # 従来のサブプロセスモード
    def run_system(input_data, db_path=None):
        """元のサブプロセス実装"""
        env = os.environ.copy()
        if db_path:
            env["RGL_DATABASE_PATH"] = db_path
            
        python_cmd = sys.executable
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        result = subprocess.run(
            [python_cmd, "-m", "requirement.graph"],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            env=env,
            cwd=project_root
        )
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in reversed(lines):
                if line.strip():
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
                        
        return {"error": "No valid JSON output", "stderr": result.stderr}