"""
Cypherテンプレートの動作確認テスト（TDD Red）

bin/docsの規約に従い、テンプレートベースのアプローチを採用
- 単純なCRUD操作はテンプレートテストで確認
- 複雑なビジネスロジックは別途定型メソッドテストで確認
"""
import pytest
from pathlib import Path
from typing import Callable
from .infrastructure.kuzu_repository import create_kuzu_repository
from .infrastructure.ddl_schema_manager import DDLSchemaManager


class TestVersionTemplates:
    """バージョン管理用Cypherテンプレートのテスト"""

    @pytest.fixture
    def repo(self, tmp_path):
        """テスト用リポジトリ"""
        from .infrastructure.variables import enable_test_mode
        enable_test_mode()

        db_path = tmp_path / "test.db"
        repo = create_kuzu_repository(str(db_path))

        # スキーマ適用
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = Path(__file__).parent / "ddl" / "migrations" / "3.2.0_current.cypher"
        if schema_path.exists():
            success, results = schema_manager.apply_schema(str(schema_path))
            assert success

        return repo

    @pytest.fixture
    def template_loader(self) -> Callable[[str, str], str]:
        """テンプレートローダー（純粋関数）"""
        def load_template(category: str, name: str) -> str:
            # 既存のテンプレートパスを使用
            base_path = Path("/home/nixos/bin/src/kuzu/query")
            path = base_path / category / f"{name}.cypher"
            if path.exists():
                return path.read_text()

            # 新規テンプレートパス
            new_path = Path(__file__).parent / "query" / category / f"{name}.cypher"
            if new_path.exists():
                return new_path.read_text()

            raise FileNotFoundError(f"Template not found: {category}/{name}")
        return load_template

    def test_create_versionstate_template(self, repo, template_loader):
        """create_versionstate.cypherの動作確認"""
        template = template_loader("dml", "create_versionstate")
        params = {
            "id": "ver_001",
            "timestamp": "2024-01-01T00:00:00Z",
            "description": "初回作成",
            "change_reason": "新規要件",
            "progress_percentage": 0.0
        }
        result = repo["connection"].execute(template, params)
        assert result.has_next()

    def test_version_state_history_template(self, repo, template_loader):
        """version_state_history.cypherの動作確認"""
        # 事前データ作成
        create_template = template_loader("dml", "create_versionstate")
        for i in range(3):
            params = {
                "id": f"ver_{i:03d}",
                "timestamp": f"2024-01-{i+1:02d}T00:00:00Z",
                "description": f"バージョン{i+1}",
                "change_reason": f"更新{i+1}",
                "progress_percentage": i * 0.3
            }
            repo["connection"].execute(create_template, params)

        # 履歴取得
        history_template = template_loader("dql", "version_state_history")
        result = repo["connection"].execute(history_template, {})

        # 結果確認
        versions = []
        while result.has_next():
            versions.append(result.get_next())

        assert len(versions) == 3
        assert versions[0][0] == "ver_000"  # version_id
        assert versions[1][0] == "ver_001"
        assert versions[2][0] == "ver_002"



    def test_create_versioned_requirement_template(self, repo, template_loader):
        """create_versioned_requirement.cypherの動作確認"""
        template = template_loader("dml", "create_versioned_requirement")
        params = {
            "req_id": "REQ-001",
            "title": "テスト要件",
            "description": "説明",
            "status": "draft",
            "author": "test_user",
            "reason": "初回作成",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        result = repo["connection"].execute(template, params)
        assert result.has_next()
        row = result.get_next()
        assert row[0] == "REQ-001"  # entity_id (not REQ-001_v_)
        assert row[1] == "ver_REQ-001_v1"  # version_id
        assert row[2] == "req://REQ-001"  # location_uri

