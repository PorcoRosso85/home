"""
ASVS Arrow Type Definitions

Arrow Tableのスキーマに対応する型定義
"""
from typing import TypedDict, List, Optional
import pyarrow as pa


class ASVSRequirementRow(TypedDict):
    """Arrow Table内の1行を表す型"""
    uri: str
    number: str
    description: str
    level1: bool
    level2: bool
    level3: bool
    section: str
    chapter: str
    tags: Optional[List[str]]
    cwe: Optional[List[int]]
    nist: Optional[List[str]]


class ASVSMetadata(TypedDict):
    """Arrow Tableのメタデータ"""
    source: str  # 'OWASP/ASVS'
    version: str  # '5.0'
    total_requirements: int
    levels: List[int]  # [1, 2, 3]
    schema_version: str  # '1.0'


# Pyarrowスキーマとの対応を保証する定数
ASVS_ARROW_SCHEMA = pa.schema([
    ('uri', pa.string()),
    ('number', pa.string()),
    ('description', pa.string()),
    ('level1', pa.bool_()),
    ('level2', pa.bool_()),
    ('level3', pa.bool_()),
    ('section', pa.string()),
    ('chapter', pa.string()),
    ('tags', pa.list_(pa.string())),
    ('cwe', pa.list_(pa.int32())),
    ('nist', pa.list_(pa.string()))
])