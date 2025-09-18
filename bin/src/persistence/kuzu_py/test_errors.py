"""
エラー型のテスト
"""
import pytest
from errors import FileOperationError, ValidationError, NotFoundError


def test_file_operation_error_creation():
    """FileOperationErrorの作成テスト"""
    error = FileOperationError(
        type="FileOperationError",
        message="File not found",
        operation="read",
        file_path="/path/to/file",
        permission_issue=False,
        exists=False
    )
    
    assert error["type"] == "FileOperationError"
    assert error["message"] == "File not found"
    assert error["operation"] == "read"
    assert error["file_path"] == "/path/to/file"
    assert error["permission_issue"] is False
    assert error["exists"] is False


def test_validation_error_creation():
    """ValidationErrorの作成テスト"""
    error = ValidationError(
        type="ValidationError",
        message="Invalid value",
        field="query_type",
        value="invalid",
        constraint="Must be dml or dql",
        suggestion="Use 'auto' for automatic detection"
    )
    
    assert error["type"] == "ValidationError"
    assert error["message"] == "Invalid value"
    assert error["field"] == "query_type"
    assert error["value"] == "invalid"
    assert error["constraint"] == "Must be dml or dql"
    assert error["suggestion"] == "Use 'auto' for automatic detection"


def test_not_found_error_creation():
    """NotFoundErrorの作成テスト"""
    error = NotFoundError(
        type="NotFoundError",
        message="Query not found",
        resource_type="query",
        resource_id="test_query",
        search_locations=["/queries/dml", "/queries/dql"]
    )
    
    assert error["type"] == "NotFoundError"
    assert error["message"] == "Query not found"
    assert error["resource_type"] == "query"
    assert error["resource_id"] == "test_query"
    assert error["search_locations"] == ["/queries/dml", "/queries/dql"]


def test_optional_fields():
    """オプションフィールドのテスト"""
    # FileOperationErrorでオプションフィールドを省略
    error = FileOperationError(
        type="FileOperationError",
        message="Error",
        operation="write",
        file_path="/path",
        permission_issue=None,
        exists=None
    )
    assert error["permission_issue"] is None
    assert error["exists"] is None
    
    # ValidationErrorでsuggestionを省略
    error = ValidationError(
        type="ValidationError",
        message="Error",
        field="field",
        value="value",
        constraint="constraint",
        suggestion=None
    )
    assert error["suggestion"] is None
    
    # NotFoundErrorでsearch_locationsを省略
    error = NotFoundError(
        type="NotFoundError",
        message="Not found",
        resource_type="type",
        resource_id="id",
        search_locations=None
    )
    assert error["search_locations"] is None


def test_error_type_discrimination():
    """エラー型の判別テスト"""
    file_error = FileOperationError(
        type="FileOperationError",
        message="File error",
        operation="read",
        file_path="/path",
        permission_issue=False,
        exists=True
    )
    
    validation_error = ValidationError(
        type="ValidationError",
        message="Validation error",
        field="field",
        value="value",
        constraint="constraint",
        suggestion=None
    )
    
    not_found_error = NotFoundError(
        type="NotFoundError",
        message="Not found",
        resource_type="resource",
        resource_id="id",
        search_locations=None
    )
    
    # 型判別
    assert file_error["type"] == "FileOperationError"
    assert validation_error["type"] == "ValidationError"
    assert not_found_error["type"] == "NotFoundError"
    
    # isinstance()は使えない（TypedDictはランタイムでは普通のdict）
    # 代わりにtypeフィールドで判別
    errors = [file_error, validation_error, not_found_error]
    for error in errors:
        assert isinstance(error, dict)
        assert "type" in error
        assert "message" in error