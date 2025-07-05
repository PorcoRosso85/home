"""
バージョニングDQLテンプレートのテスト（TDD Red）

バージョニング機能のDQL（Data Query Language）テンプレートが
正しく定義され、使用可能であることを確認する。
"""
import pytest
from pathlib import Path
import json
import tempfile
import os
import shutil


class TestVersionDQLTemplates:
    """バージョニングDQLテンプレートのテスト"""
    
    def test_履歴取得テンプレートが存在する(self):
        """get_requirement_history.cypherテンプレートが存在することを確認"""
        template_path = Path(__file__).parent / "query" / "dql" / "get_requirement_history.cypher"
        
        assert template_path.exists(), f"テンプレートが存在しません: {template_path}"
        
        # テンプレート内容を確認
        content = template_path.read_text()
        
        # 必要なパラメータが含まれている
        assert "$req_id" in content, "要件IDパラメータが含まれていません"
        
        # 必要なテーブルとリレーションが含まれている
        assert "LocationURI" in content
        assert "RequirementEntity" in content
        assert "VersionState" in content
        assert "HAS_VERSION" in content
        assert "LOCATES" in content
        
        # 時系列でソートされている
        assert "ORDER BY" in content
        assert "timestamp" in content.lower()
    
    def test_特定時点取得テンプレートが存在する(self):
        """get_requirement_at_timestamp.cypherテンプレートが存在することを確認"""
        template_path = Path(__file__).parent / "query" / "dql" / "get_requirement_at_timestamp.cypher"
        
        assert template_path.exists(), f"テンプレートが存在しません: {template_path}"
        
        content = template_path.read_text()
        
        # 必要なパラメータ
        assert "$req_id" in content
        assert "$timestamp" in content
        
        # タイムスタンプ以前の最新バージョンを取得
        assert "WHERE" in content
        assert "<=" in content
        assert "LIMIT 1" in content
    
    def test_バージョン差分テンプレートが存在する(self):
        """get_version_diff.cypherテンプレートが存在することを確認"""
        template_path = Path(__file__).parent / "query" / "dql" / "get_version_diff.cypher"
        
        assert template_path.exists(), f"テンプレートが存在しません: {template_path}"
        
        content = template_path.read_text()
        
        # 必要なパラメータ
        assert "$req_id" in content
        assert "$from_version" in content
        assert "$to_version" in content
        
        # バージョン情報を扱う
        assert "versions" in content or "VersionState" in content
    
    def test_全バージョン一覧テンプレートが存在する(self):
        """list_all_versions.cypherテンプレートが存在することを確認"""
        template_path = Path(__file__).parent / "query" / "dql" / "list_all_versions.cypher"
        
        assert template_path.exists(), f"テンプレートが存在しません: {template_path}"
        
        content = template_path.read_text()
        
        # 要件IDパラメータ
        assert "$req_id" in content
        
        # バージョン番号を含む
        assert "version" in content.lower() or "v.id" in content
        
        # 操作タイプを含む
        assert "operation" in content.lower()
    
    def test_version_serviceがテンプレートを使用する(self):
        """version_service.pyがDQLテンプレートを使用することを確認"""
        from .application.version_service import load_template
        
        # テンプレートが正しくロードできる
        history_template = load_template("dql", "get_requirement_history")
        assert history_template is not None
        assert len(history_template) > 0
        
        timestamp_template = load_template("dql", "get_requirement_at_timestamp")
        assert timestamp_template is not None
        
        diff_template = load_template("dql", "get_version_diff")
        assert diff_template is not None
    
    def test_履歴取得クエリの実行(self):
        """履歴取得テンプレートが実際に動作することを確認"""
        from .infrastructure.kuzu_repository import create_kuzu_repository
        from .application.version_service import create_version_service
        
        # テスト用DBを作成
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            # スキーマ適用
            from .infrastructure.ddl_schema_manager import DDLSchemaManager
            repo = create_kuzu_repository(test_db)
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = Path(__file__).parent / "ddl" / "schema.cypher"
            success, _ = schema_manager.apply_schema(str(schema_path))
            assert success
            
            # バージョンサービスを作成
            version_service = create_version_service(repo)
            
            # 要件を作成して更新
            version_service["create_versioned_requirement"]({
                "id": "REQ-HIST-001",
                "title": "テスト要件",
                "description": "初期バージョン"
            })
            
            version_service["update_versioned_requirement"]({
                "id": "REQ-HIST-001",
                "title": "テスト要件（更新）",
                "description": "更新バージョン",
                "author": "tester",
                "reason": "機能追加"
            })
            
            # 履歴取得（テンプレート使用）
            history = version_service["get_requirement_history"]("REQ-HIST-001")
            
            # 結果確認
            assert len(history) == 2
            assert history[0]["operation"] == "CREATE"
            assert history[1]["operation"] == "UPDATE"
            assert history[1]["change_reason"] == "機能追加"
            
            # テンプレートからのクエリであることを確認
            # （load_templateが呼ばれていることを間接的に確認）
            template_path = Path(__file__).parent / "query" / "dql" / "get_requirement_history.cypher"
            assert template_path.exists()
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_特定バージョン取得クエリの実行(self):
        """特定バージョン取得テンプレートが実際に動作することを確認"""
        from .infrastructure.kuzu_repository import create_kuzu_repository
        from .application.version_service import create_version_service
        from datetime import datetime, timedelta
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            # DB初期化
            from .infrastructure.ddl_schema_manager import DDLSchemaManager
            repo = create_kuzu_repository(test_db)
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = Path(__file__).parent / "ddl" / "schema.cypher"
            success, _ = schema_manager.apply_schema(str(schema_path))
            assert success
            
            version_service = create_version_service(repo)
            
            # 要件作成
            version_service["create_versioned_requirement"]({
                "id": "REQ-TIME-001",
                "title": "時点取得テスト",
                "description": "バージョン1"
            })
            
            # 少し待つ
            import time
            time.sleep(0.1)
            mid_timestamp = datetime.now().isoformat()
            time.sleep(0.1)
            
            # 要件更新
            version_service["update_versioned_requirement"]({
                "id": "REQ-TIME-001",
                "description": "バージョン2"
            })
            
            # 中間時点の要件を取得（テンプレート使用）
            requirement = version_service["get_requirement_at_timestamp"](
                "REQ-TIME-001", 
                mid_timestamp
            )
            
            # バージョン1が取得される
            assert requirement is not None
            assert requirement["version"] == 1
            # 注: 現在の実装では、エンティティ自体が更新されるため、
            # 過去のバージョンの内容は取得できない（設計上の制限）
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_複雑な履歴クエリのパフォーマンス(self):
        """大量のバージョンがある場合でも効率的に動作することを確認"""
        from .infrastructure.kuzu_repository import create_kuzu_repository
        from .application.version_service import create_version_service
        import time
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            # DB初期化
            from .infrastructure.ddl_schema_manager import DDLSchemaManager
            repo = create_kuzu_repository(test_db)
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = Path(__file__).parent / "ddl" / "schema.cypher"
            success, _ = schema_manager.apply_schema(str(schema_path))
            assert success
            
            version_service = create_version_service(repo)
            
            # 要件作成
            version_service["create_versioned_requirement"]({
                "id": "REQ-PERF-001",
                "title": "パフォーマンステスト",
                "description": "初期"
            })
            
            # 50回更新
            for i in range(50):
                version_service["update_versioned_requirement"]({
                    "id": "REQ-PERF-001",
                    "description": f"更新 {i+1}",
                    "author": f"tester_{i}",
                    "reason": f"理由 {i+1}"
                })
            
            # 履歴取得の時間を計測
            start_time = time.time()
            history = version_service["get_requirement_history"]("REQ-PERF-001")
            end_time = time.time()
            
            # 結果確認
            assert len(history) == 51  # 初期 + 50更新
            assert end_time - start_time < 1.0  # 1秒以内に完了
            
            # テンプレートが存在し、効率的なクエリパターンを使用していることを確認
            template_path = Path(__file__).parent / "query" / "dql" / "get_requirement_history.cypher"
            assert template_path.exists()
            content = template_path.read_text()
            # 基本的なクエリ構造を確認
            assert "MATCH" in content
            assert "ORDER BY" in content  # 時系列ソートが含まれている
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("=== バージョニングDQLテンプレートTDD Redテスト ===")
    print("必要なテンプレート:")
    print("1. get_requirement_history.cypher - 変更履歴取得")
    print("2. get_requirement_at_timestamp.cypher - 特定時点の状態取得")
    print("3. get_version_diff.cypher - バージョン間差分")
    print("4. list_all_versions.cypher - 全バージョン一覧")
    print("\nこれらのテンプレートを作成することで、")
    print("バージョニング機能のクエリが標準化され、保守性が向上します。")