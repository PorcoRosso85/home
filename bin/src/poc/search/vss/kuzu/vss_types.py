#!/usr/bin/env python3
"""Type definitions for VSS module"""

from typing import List, Dict, Any, Union, Literal, TypedDict


class IndexSuccess(TypedDict):
    ok: Literal[True]
    message: str


class IndexError(TypedDict):
    ok: Literal[False]
    error: str


IndexResult = Union[IndexSuccess, IndexError]


class SearchSuccess(TypedDict):
    ok: Literal[True]
    results: List[Dict[str, Any]]


class SearchError(TypedDict):
    ok: Literal[False]
    error: str


SearchResult = Union[SearchSuccess, SearchError]


class EmbeddingSuccess(TypedDict):
    ok: Literal[True]
    embedding: List[float]


class EmbeddingError(TypedDict):
    ok: Literal[False]
    error: str


EmbeddingResult = Union[EmbeddingSuccess, EmbeddingError]


class ExistsSuccess(TypedDict):
    ok: Literal[True]
    exists: bool


class ExistsError(TypedDict):
    ok: Literal[False]
    error: str


ExistsResult = Union[ExistsSuccess, ExistsError]


class CountSuccess(TypedDict):
    ok: Literal[True]
    indexed_count: int


class CountError(TypedDict):
    ok: Literal[False]
    error: str


CountResult = Union[CountSuccess, CountError]
