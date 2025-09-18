from typing import TypedDict, Union, Any, List, Dict, Optional


class ErrorDict(TypedDict):
    error: str
    details: Optional[str]
    traceback: Optional[str]


class JsonOperationResult(TypedDict):
    success: bool
    data: Optional[Any]
    error: Optional[str]


class DatabaseConfig(TypedDict):
    path: str


class QueryResult(TypedDict):
    columns: List[str]
    rows: List[List[Any]]


JsonValue = Union[None, bool, int, float, str, List["JsonValue"], Dict[str, "JsonValue"]]