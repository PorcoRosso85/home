"""
requirement/graph domain types - 純粋な型定義
外部依存: なし
"""
from typing import TypedDict, Literal, Union, List, Any, Dict, Optional
from datetime import datetime


# Decision型定義
class Decision(TypedDict):
    """開発決定事項の型定義"""
    id: str
    title: str
    description: str
    status: Literal["proposed", "approved", "implemented", "deprecated"]
    created_at: datetime
    embedding: List[float]  # 50次元ベクトル


# Error型定義
class DecisionNotFoundError(TypedDict):
    """決定事項が見つからないエラー"""
    type: Literal["DecisionNotFoundError"]
    message: str
    decision_id: str


class InvalidDecisionError(TypedDict):
    """不正な決定事項エラー"""
    type: Literal["InvalidDecisionError"]
    message: str
    details: List[str]


class EmbeddingError(TypedDict):
    """埋め込み生成エラー"""
    type: Literal["EmbeddingError"]
    message: str
    text: str


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
DecisionError = Union[DecisionNotFoundError, InvalidDecisionError, EmbeddingError]
DecisionResult = Union[Decision, DecisionError]
QueryResult = Union[QuerySuccess, QueryError]


