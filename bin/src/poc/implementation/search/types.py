"""
検索結果の型定義
bin/docs/conventions に従い、TypedDictを使用してデータ構造を定義
"""

from typing import TypedDict, Optional, List, Literal


class SymbolDict(TypedDict):
    """シンボル情報の型定義"""
    name: str
    type: Literal["function", "class", "method", "variable", "constant", "import", "type_alias"]
    path: str
    line: int
    column: Optional[int]
    context: Optional[str]


class MetadataDict(TypedDict):
    """メタデータの型定義"""
    searched_files: int
    search_time_ms: float
    provider: Optional[str]


class SearchSuccessDict(TypedDict):
    """検索成功時の結果"""
    symbols: List[SymbolDict]
    metadata: MetadataDict


class SearchErrorDict(TypedDict):
    """検索エラー時の結果"""
    error: str
    metadata: MetadataDict


# conventionに従い、成功型とエラー型のUnion
SearchResult = SearchSuccessDict | SearchErrorDict