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

from .domain.types import (
    QueryError,
    QuerySuccess,
    QueryResult
)

from .domain.error_types import (
    ErrorExample,
    ErrorGuidance,
    UserFriendlyError,
    RecoveryGuidance
)

from .domain.errors import (
    EnvironmentConfigError,
    DatabaseError,
    FileOperationError,
    ImportError,
    ValidationError,
    NotFoundError
)

# Application層
from .application.search_adapter import SearchAdapter
from .application.template_processor import process_template
from .application.error_handler import create_error_handler

# Infrastructure層
from .infrastructure.kuzu_repository import create_kuzu_repository
from .infrastructure.jsonl_repository import create_jsonl_repository
from .infrastructure.apply_ddl_schema import apply_ddl_schema
from .infrastructure.ddl_schema_manager import DDLSchemaManager
# from .infrastructure.hierarchy_validator import HierarchyValidator  # 削除済み

__all__ = [
    # Domain - Constraints
    "ConstraintViolationError",
    "validate_no_circular_dependency",
    "validate_max_depth",
    "validate_implementation_completeness",
    # Domain - Types
    "QueryError",
    "QuerySuccess",
    "QueryResult",
    # Domain - Error Types
    "ErrorExample",
    "ErrorGuidance",
    "UserFriendlyError",
    "RecoveryGuidance",
    # Domain - Errors
    "EnvironmentConfigError",
    "DatabaseError",
    "FileOperationError",
    "ImportError",
    "ValidationError",
    "NotFoundError",
    # Application
    "SearchAdapter",
    "process_template",
    "create_error_handler",
    # Infrastructure
    "create_kuzu_repository",
    "create_jsonl_repository",
    "apply_ddl_schema",
    "DDLSchemaManager"
]
