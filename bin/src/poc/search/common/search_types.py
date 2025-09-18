#!/usr/bin/env python3
"""
検索システムの型定義（TypedDict使用、規約で許可）
"""

from typing import TypedDict, List, Optional


class RequirementSearchResult(TypedDict):
    """要件検索結果"""

    id: str
    title: str
    description: str
    similarity_rank: Optional[int]
    sources: Optional[List[str]]
    match_type: Optional[str]


class VectorIndexResult(TypedDict):
    """ベクトルインデックス作成結果"""

    success: bool
    index_name: str
    error: Optional[str]


class FTSIndexResult(TypedDict):
    """FTSインデックス作成結果"""

    success: bool
    index_name: str
    error: Optional[str]
