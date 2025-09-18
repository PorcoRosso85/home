"""
LocationURI Dataset Management テスト
"""
import pytest
from mod import (
    create_locationuri_dataset,
    validate_locationuri,
    create_restricted_repository
)


class TestLocationURIDataset:
    """LocationURIデータセット機能のテスト"""
    
    def test_create_dataset_returns_valid_structure(self):
        """データセット作成が適切な構造を返すこと"""
        result = create_locationuri_dataset()
        
        assert "uris" in result
        assert "metadata" in result
        assert isinstance(result["uris"], list)
        assert len(result["uris"]) > 0
        assert all(uri.startswith("req://") for uri in result["uris"])
    
    def test_dataset_contains_expected_categories(self):
        """データセットが期待されるカテゴリを含むこと"""
        result = create_locationuri_dataset()
        metadata = result["metadata"]
        
        assert metadata["total"] == len(result["uris"])
        assert "categories" in metadata
        
        categories = metadata["categories"]
        assert categories["root"] == 5
        assert categories["architecture"] == 4
        assert categories["security"] == 4
        assert categories["performance"] == 4
        assert categories["project"] == 3


class TestLocationURIValidation:
    """LocationURI検証機能のテスト"""
    
    def test_validate_correct_uri_format(self):
        """正しいURI形式を受け入れること"""
        result = validate_locationuri("req://system")
        assert result["valid"] is True
        assert "Valid" in result["reason"]
    
    def test_reject_invalid_prefix(self):
        """不正なプレフィックスを拒否すること"""
        result = validate_locationuri("http://system")
        assert result["valid"] is False
        assert "must start with 'req://'" in result["reason"]
    
    def test_reject_empty_path(self):
        """空のパスを拒否すること"""
        result = validate_locationuri("req://")
        assert result["valid"] is False
        assert "cannot be empty" in result["reason"]
    
    def test_reject_invalid_characters(self):
        """不正な文字を含むURIを拒否すること"""
        invalid_uris = [
            "req://system\\path",
            "req://system with space",
            "req://system\npath",
            "req://system..path",
            "req://system//path"
        ]
        
        for uri in invalid_uris:
            result = validate_locationuri(uri)
            assert result["valid"] is False
            assert "invalid character" in result["reason"]
    
    def test_dataset_restriction(self):
        """データセット制限が機能すること"""
        allowed = {"req://system", "req://architecture"}
        
        # 許可されたURI
        result = validate_locationuri("req://system", allowed)
        assert result["valid"] is True
        
        # 許可されていないURI
        result = validate_locationuri("req://unknown", allowed)
        assert result["valid"] is False
        assert "not in the allowed dataset" in result["reason"]


class TestRestrictedRepository:
    """制限付きリポジトリのテスト"""
    
    def test_create_repository_success(self):
        """リポジトリ作成が成功すること"""
        repo = create_restricted_repository(":memory:")
        
        # エラーでないことを確認
        assert "type" not in repo or "Error" not in repo.get("type", "")
        
        # 必要な関数が存在すること
        assert "create_locationuri_node" in repo
        assert "list_locationuris" in repo
        assert "get_allowed_dataset" in repo
        assert "validate_locationuri" in repo
    
    def test_allowed_dataset_loaded(self):
        """許可されたデータセットがロードされること"""
        repo = create_restricted_repository(":memory:")
        
        result = repo["get_allowed_dataset"]()
        assert result["type"] == "Success"
        assert len(result["uris"]) > 0
        assert all(uri.startswith("req://") for uri in result["uris"])
    
    def test_create_allowed_node(self):
        """許可されたURIのノード作成が成功すること"""
        repo = create_restricted_repository(":memory:")
        
        # データセットから最初のURIを取得
        dataset = repo["get_allowed_dataset"]()
        first_uri = dataset["uris"][0]
        
        # 作成を試行
        result = repo["create_locationuri_node"](first_uri)
        
        # AlreadyExistsの場合も成功とみなす（初期ロード済み）
        assert result["type"] in ["Success", "AlreadyExists"]
    
    def test_reject_non_dataset_node(self):
        """データセット外のURIを拒否すること"""
        repo = create_restricted_repository(":memory:")
        
        # データセットに含まれないURI
        result = repo["create_locationuri_node"]("req://not/in/dataset")
        
        assert result["type"] == "ValidationError"
        assert "not in the allowed dataset" in result["message"]
    
    def test_list_nodes(self):
        """ノード一覧取得が機能すること"""
        repo = create_restricted_repository(":memory:")
        
        result = repo["list_locationuris"]()
        assert result["type"] == "Success"
        assert "uris" in result
        assert "count" in result
        
        # 初期データセットがロードされているはず
        assert result["count"] > 0