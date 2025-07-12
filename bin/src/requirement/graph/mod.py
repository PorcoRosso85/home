"""
要件グラフ管理システム - モジュールエクスポート

使用例:
    # KuzuDBベースの要件管理
    from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository

    repo = create_kuzu_repository()

    # 要件を保存
    requirement = {
        "id": "req_001",
        "title": "ユーザー認証",
        "description": "OAuth2による認証実装",
        "status": "proposed",
        "created_at": datetime.now()
    }

    result = repo["save"](requirement)

    # 依存関係を追加
    repo["add_dependency"]("req_001", "req_002", "technical")

"""

# Domain層

from .domain.constraints import (
    ConstraintViolationError,
    validate_no_circular_dependency,
    validate_max_depth,
    validate_implementation_completeness
)


# Application層

# Infrastructure層
from .infrastructure.kuzu_repository import create_kuzu_repository
from .infrastructure.jsonl_repository import create_jsonl_repository
from .infrastructure.apply_ddl_schema import apply_ddl_schema
from .infrastructure.ddl_schema_manager import DDLSchemaManager
# from .infrastructure.hierarchy_validator import HierarchyValidator  # 削除済み

__all__ = [
    # Domain
    "ConstraintViolationError",
    "validate_no_circular_dependency",
    "validate_max_depth",
    "validate_implementation_completeness",
    # Application
    # Infrastructure
    "create_kuzu_repository",
    "create_jsonl_repository",
    "apply_ddl_schema",
    "DDLSchemaManager"
]
