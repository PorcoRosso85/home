"""
analyze_jsonlの型定義

CONVENTION.yaml準拠:
- TypedDictで不変データ構造を定義
- 具体的な型でエラーを表現
- ハードコード値は型で表現
"""

from typing import TypedDict, List, Any, Union, Literal


class QueryResultData(TypedDict):
    """クエリ結果のデータ構造"""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float


class QuerySuccessResult(TypedDict):
    """クエリ成功時の結果"""
    ok: Literal[True]
    data: QueryResultData


class QueryErrorResult(TypedDict):
    """クエリエラー時の結果"""
    ok: Literal[False]
    error: str


# エラーを値として扱う（CONVENTION.yaml準拠）
QueryResult = Union[QuerySuccessResult, QueryErrorResult]


class RegisterSuccessResult(TypedDict):
    """ファイル登録成功時の結果"""
    ok: Literal[True]
    registered_count: int
    view_name: str


class RegisterErrorResult(TypedDict):
    """ファイル登録エラー時の結果"""
    ok: Literal[False]
    error: str


RegisterResult = Union[RegisterSuccessResult, RegisterErrorResult]


class UnifiedViewSuccessResult(TypedDict):
    """統合ビュー作成成功時の結果"""
    ok: Literal[True]
    view_name: str
    source_count: int


class UnifiedViewErrorResult(TypedDict):
    """統合ビュー作成エラー時の結果"""
    ok: Literal[False]
    error: str


UnifiedViewResult = Union[UnifiedViewSuccessResult, UnifiedViewErrorResult]


class AnalyzerCreateResult(TypedDict):
    """アナライザー作成エラー時の結果"""
    ok: Literal[False]
    error: str


# ====================
# REDフェーズ: 型定義のテスト
# ====================

def test_query_result_data_型定義_必須フィールド存在():
    """QueryResultData型が必要なフィールドを持つ"""
    data: QueryResultData = {
        'columns': ['col1', 'col2'],
        'rows': [['val1', 'val2']],
        'row_count': 1,
        'execution_time_ms': 10.5
    }
    assert 'columns' in data
    assert 'rows' in data
    assert 'row_count' in data
    assert 'execution_time_ms' in data


def test_query_success_result_型定義_ok_true():
    """QuerySuccessResult型のokフィールドがTrue"""
    result: QuerySuccessResult = {
        'ok': True,
        'data': {
            'columns': [],
            'rows': [],
            'row_count': 0,
            'execution_time_ms': 0.0
        }
    }
    assert result['ok'] is True
    assert 'data' in result


def test_query_error_result_型定義_ok_false():
    """QueryErrorResult型のokフィールドがFalse"""
    result: QueryErrorResult = {
        'ok': False,
        'error': 'テストエラー'
    }
    assert result['ok'] is False
    assert 'error' in result