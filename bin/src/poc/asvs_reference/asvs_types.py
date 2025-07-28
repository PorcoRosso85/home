"""
ASVS Reference Type Definitions

Provides type-safe interfaces for ASVS data structures
to be used by other POCs as a data provider.
"""
from typing import TypedDict, List, Optional, Union, Literal


class ASVSRequirement(TypedDict):
    """Individual ASVS requirement"""
    uri: str
    number: str
    description: str
    level1: bool
    level2: bool
    level3: bool
    section_uri: str
    tags: Optional[List[str]]
    cwe: Optional[List[int]]
    nist: Optional[str]


class ASVSSection(TypedDict):
    """ASVS section containing requirements"""
    uri: str
    number: str
    name: str
    chapter_uri: str
    requirements: List[ASVSRequirement]


class ASVSChapter(TypedDict):
    """ASVS chapter containing sections"""
    uri: str
    number: str
    name: str
    standard_uri: str
    sections: List[ASVSSection]


class ASVSStandard(TypedDict):
    """Complete ASVS standard"""
    uri: str
    name: str
    version: str
    description: str
    url: str
    chapters: List[ASVSChapter]


# Search result types
class RequirementSearchResult(TypedDict):
    """Search result for requirements"""
    requirements: List[ASVSRequirement]
    total_count: int
    query: str


# API response types
SuccessResponse = TypedDict('SuccessResponse', {
    'type': Literal['Success'],
    'value': Union[ASVSRequirement, List[ASVSRequirement], RequirementSearchResult]
})

ErrorResponse = TypedDict('ErrorResponse', {
    'type': Literal['Error'],
    'error': str,
    'message': str,
    'details': Optional[dict]
})

APIResponse = Union[SuccessResponse, ErrorResponse]


# Filter types
class LevelFilter(TypedDict, total=False):
    """Filter requirements by ASVS level"""
    level1: Optional[bool]
    level2: Optional[bool]
    level3: Optional[bool]


class SearchFilter(TypedDict, total=False):
    """Search filter options"""
    keyword: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    levels: Optional[LevelFilter]
    limit: Optional[int]
    offset: Optional[int]