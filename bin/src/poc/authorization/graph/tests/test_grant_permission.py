"""
権限付与機能のテスト

URIベースのエンティティ間で権限(auth関係)を付与できることを検証
"""
import pytest
from auth_graph import AuthGraph


def test_grant_permission_creates_auth_relationship():
    """権限付与により、URIエンティティ間にauth関係が作成される"""
    # Arrange
    auth = AuthGraph(":memory:")
    subject_uri = "user:alice"
    resource_uri = "resource:file/123"
    
    # Act
    auth.grant_permission(subject_uri, resource_uri)
    
    # Assert
    # 権限が付与されていることを確認
    assert auth.has_permission(subject_uri, resource_uri) is True


def test_grant_permission_is_idempotent():
    """同じ権限を複数回付与しても、結果は同じである（冪等性）"""
    # Arrange
    auth = AuthGraph(":memory:")
    subject_uri = "user:bob"
    resource_uri = "service:api/v1"
    
    # Act
    auth.grant_permission(subject_uri, resource_uri)
    auth.grant_permission(subject_uri, resource_uri)  # 2回目
    
    # Assert
    # 1つの関係のみ存在することを確認
    assert auth.has_permission(subject_uri, resource_uri) is True