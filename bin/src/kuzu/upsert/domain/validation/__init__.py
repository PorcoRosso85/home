"""
検証モジュール

このモジュールは、データ検証のための様々な機能を提供します。
"""

from upsert.domain.validation.types import (
    SHACLValidationResult,
    ValidationDetails,
    is_shacl_valid,
    is_shacl_error,
)

from upsert.domain.validation.shacl_validator import (
    validate_against_shacl,
    load_shapes_file,
    analyze_validation_report,
)

# モジュールのバージョン
__version__ = "0.1.0"

# 公開API
__all__ = [
    "SHACLValidationResult",
    "ValidationDetails",
    "is_shacl_valid",
    "is_shacl_error",
    "validate_against_shacl",
    "load_shapes_file",
    "analyze_validation_report",
]
