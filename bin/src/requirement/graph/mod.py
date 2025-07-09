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
        "created_at": datetime.now(),
        "embedding": [0.1] * 50
    }
    
    result = repo["save"](requirement)
    
    # 依存関係を追加
    repo["add_dependency"]("req_001", "req_002", "technical")
    
    # 最適化機能を使用
    from requirement.graph.application.optimization_features import (
        optimize_implementation_order_with_layers,
        estimate_effort
    )
    
    order = optimize_implementation_order_with_layers(
        requirements, code_entities, relations, dependencies
    )
"""

# Domain層
from .domain.types import (
    Decision,
    DecisionResult,
    DecisionError,
    DecisionNotFoundError
)

from .domain.decision import (
    create_decision
)

from .domain.constraints import (
    ConstraintViolationError,
    validate_no_circular_dependency,
    validate_max_depth,
    validate_implementation_completeness
)

from .domain.version_tracking import (
    create_location_uri,
    create_version_id,
    create_requirement_snapshot,
    parse_location_uri
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
    "Decision",
    "DecisionResult",
    "DecisionError",
    "DecisionNotFoundError",
    "ConstraintViolationError",
    "create_decision",
    "validate_no_circular_dependency",
    "validate_max_depth",
    "validate_implementation_completeness",
    "create_location_uri",
    "create_version_id",
    "create_requirement_snapshot",
    "parse_location_uri",
    # Application
    # Infrastructure
    "create_kuzu_repository",
    "create_jsonl_repository",
    "apply_ddl_schema",
    "DDLSchemaManager"
]
