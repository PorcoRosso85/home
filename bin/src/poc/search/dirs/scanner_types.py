#!/usr/bin/env python3
"""ディレクトリスキャナーの型定義"""

from typing import TypedDict, Union, Literal, List, Dict, Optional


# ディレクトリ情報
class DirectoryInfo(TypedDict):
    path: str
    has_readme: bool
    file_count: int
    subdirs: List[str]
    metadata: Dict[str, str]  # flake.nix description等


# スキャン結果
class ScanSuccess(TypedDict):
    ok: Literal[True]
    scanned_count: int
    new_count: int
    updated_count: int
    deleted_count: int
    duration_ms: float


class ScanError(TypedDict):
    ok: Literal[False]
    error: str


ScanResult = Union[ScanSuccess, ScanError]


# 差分検知結果
class DiffSuccess(TypedDict):
    ok: Literal[True]
    added: List[str]
    modified: List[str]
    deleted: List[str]


class DiffError(TypedDict):
    ok: Literal[False]
    error: str


DiffResult = Union[DiffSuccess, DiffError]


# 検索結果
class SearchHit(TypedDict):
    path: str
    score: float
    snippet: str
    has_readme: bool


class SearchSuccess(TypedDict):
    ok: Literal[True]
    hits: List[SearchHit]
    total: int
    duration_ms: float


class SearchError(TypedDict):
    ok: Literal[False]
    error: str


SearchResult = Union[SearchSuccess, SearchError]


# インデックス操作結果
class IndexSuccess(TypedDict):
    ok: Literal[True]
    message: str


class IndexError(TypedDict):
    ok: Literal[False]
    error: str


IndexResult = Union[IndexSuccess, IndexError]


# メタデータ抽出結果
class MetadataSuccess(TypedDict):
    ok: Literal[True]
    description: Optional[str]
    source: str  # "readme", "flake", "docstring", "inferred"


class MetadataError(TypedDict):
    ok: Literal[False]
    error: str


MetadataResult = Union[MetadataSuccess, MetadataError]


# DB状態
class DBStatus(TypedDict):
    total_directories: int
    indexed_directories: int
    last_scan: Optional[str]  # ISO datetime
    db_size_mb: float
