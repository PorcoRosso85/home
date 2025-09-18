"""
requirement/graph domain types - 純粋な型定義
外部依存: なし
"""
from typing import TypedDict, Literal, Union, List


# Cypher Query型定義
class QueryError(TypedDict):
    """Cypherクエリ実行エラー"""
    type: Literal["SyntaxError", "EmptyQueryError", "ConnectionError", "ValidationError"]
    message: str
    query: str


class QuerySuccess(TypedDict):
    """Cypherクエリ実行成功結果"""
    columns: List[str]
    data: List[List]
    row_count: int


# Union型
QueryResult = Union[QuerySuccess, QueryError]


