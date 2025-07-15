#!/usr/bin/env python3
"""Type definitions for FTS module"""

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


class FieldsSuccess(TypedDict):
    ok: Literal[True]
    fields: List[str]


class FieldsError(TypedDict):
    ok: Literal[False]
    error: str


FieldsResult = Union[FieldsSuccess, FieldsError]


class CountSuccess(TypedDict):
    ok: Literal[True]
    indexed_count: int


class CountError(TypedDict):
    ok: Literal[False]
    error: str


CountResult = Union[CountSuccess, CountError]
