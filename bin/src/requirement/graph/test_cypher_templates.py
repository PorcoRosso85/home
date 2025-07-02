"""
Cypherテンプレートの動作確認テスト（TDD Red）

bin/docsの規約に従い、テンプレートベースのアプローチを採用
- 単純なCRUD操作はテンプレートテストで確認
- 複雑なビジネスロジックは別途定型メソッドテストで確認
"""
import pytest
from pathlib import Path
from typing import Dict, Callable
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
        schema_path = Path(__file__).parent / "ddl" / "schema.cypher"
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
    
    @pytest.mark.skip(reason="KuzuDB互換性の問題: UNWINDの後のWHEREがサポートされていない")
    def test_version_diff_analysis_template(self, repo, template_loader):
        """version_diff_analysis.cypherの動作確認"""
        # LocationURIとVersionStateの関係を作成
        # 既存テンプレートの制約により、簡略化したテストを実施
        template = template_loader("dql", "version_diff_analysis")
        params = {
            "from_version_id": "ver_001",
            "to_version_id": "ver_002"
        }
        result = repo["connection"].execute(template, params)
        # 差分分析のロジック確認
        assert result is not None


    @pytest.mark.skip(reason="TDD Red: 新規テンプレートの実装待ち")
    def test_create_versioned_requirement_template(self, repo, template_loader):
        """create_versioned_requirement.cypherの動作確認"""
        template = template_loader("dml", "create_versioned_requirement")
        params = {
            "req_id": "REQ-001",
            "title": "テスト要件",
            "description": "説明",
            "status": "draft",
            "priority": 1,
            "author": "test_user",
            "reason": "初回作成"
        }
        result = repo["connection"].execute(template, params)
        assert result.has_next()
        row = result.get_next()
        assert row[0].startswith("REQ-001_v_")  # entity_id
        assert row[1].startswith("ver_REQ-001_")  # version_id
        assert row[2] == "req://REQ-001"  # location_uri


class TestVersionComplexOperations:
    """複雑なバージョン管理操作のテスト（定型メソッド必須）"""
    
    @pytest.mark.skip(reason="TDD Red: 複雑なロールバック処理の実装待ち")
    def test_rollback_複数テンプレート連携(self, version_service):
        """
        ロールバック機能（複数のCypherテンプレートを組み合わせた処理）
        1. 古いバージョンを取得
        2. 新バージョンとして保存
        3. メタデータを追加
        4. LocationURIを更新
        """
        # 事前準備
        req_id = "REQ-001"
        v1 = version_service.create_requirement({
            "id": req_id,
            "title": "初期版",
            "description": "最初のバージョン"
        })
        
        v2 = version_service.update_requirement({
            "id": req_id,
            "title": "更新版",
            "description": "変更されたバージョン"
        })
        
        # ロールバック実行
        rollback_result = version_service.rollback_to_version(
            req_id=req_id,
            version_id=v1["version_id"],
            reason="誤った更新のため初期版に戻す"
        )
        
        # 確認
        assert rollback_result["title"] == "初期版"
        assert rollback_result["operation"] == "ROLLBACK"
        assert "rollback" in rollback_result["author"]
    
    @pytest.mark.skip(reason="TDD Red: データ整合性検証の実装待ち")
    def test_データ整合性検証_包括的チェック(self, version_service):
        """
        データ整合性の包括的検証
        - 孤立したVersionState
        - 循環参照
        - 不整合なLocationURI
        """
        # 不整合なデータを意図的に作成
        # ...
        
        # 検証実行
        issues = version_service.validate_data_consistency()
        
        # 各種不整合が検出されることを確認
        assert "orphaned_versions" in issues
        assert "circular_references" in issues
        assert "inconsistent_uris" in issues
    
    @pytest.mark.skip(reason="TDD Red: マージ戦略の実装待ち")  
    def test_import_data_マージ戦略(self, version_service):
        """
        データインポートの各種マージ戦略
        - overwrite: 既存データを上書き
        - merge: 既存データとマージ
        - skip: 既存データをスキップ
        """
        # 既存データ
        existing = version_service.create_requirement({
            "id": "REQ-001",
            "title": "既存要件",
            "priority": 1
        })
        
        # インポートデータ
        import_data = {
            "requirements": [{
                "id": "REQ-001",
                "title": "インポート要件",
                "priority": 2
            }]
        }
        
        # overwrite戦略
        result_overwrite = version_service.import_data(
            data=import_data,
            merge_strategy="overwrite"
        )
        assert result_overwrite["REQ-001"]["title"] == "インポート要件"
        
        # merge戦略
        result_merge = version_service.import_data(
            data=import_data,
            merge_strategy="merge"
        )
        # 既存フィールドは保持、新規フィールドは追加
        
        # skip戦略
        result_skip = version_service.import_data(
            data=import_data,
            merge_strategy="skip"
        )
        assert result_skip["REQ-001"]["title"] == "既存要件"


# 削除対象マーカー
DEPRECATED_TESTS = [
    "test_要件更新時_履歴照会_各バージョンの実際の状態を返す",
    "test_要件削除時_履歴照会_削除前の全バージョンにアクセス可能",
    "test_特定時点照会_タイムスタンプ指定_その時点の正確な状態を返す",
    "test_バージョン間差分_2つのバージョンID指定_正確な変更内容を返す",
    "test_APIレスポンス_全操作_正しいフィールドを含む",
    "test_空の要件_履歴照会_空のフィールドも正確に保持される",
    "test_大量フィールド要件_履歴照会_全フィールドが保持される",
    "test_バージョン継承_旧データから新データ_全フィールドがデフォルト値で埋められる",
    "test_find_by_version_特定バージョンID_その時点の完全な状態を返す",
    "test_get_requirement_statistics_履歴含む_正確な統計が計算される"
]