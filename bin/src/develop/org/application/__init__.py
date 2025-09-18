"""Application layer - Multi-Agent Orchestration System.

This package implements the Application layer (DDD) for managing multiple AI CLI tool instances
via tmux windows with directory-based isolation.

Application API aggregation - exports all public APIs from modular components.
"""

# Import from new modular structure
from .developer import (
    start_developer,
    send_command_to_developer_by_directory,
    get_all_developers_status,
    clean_dead_developers_from_state,
)

from .designer import (
    start_designer,
    send_command_to_designer,
    send_to_designer_optimized,
)

from .history import (
    check_developer_has_history,
    get_claude_history,
)

from .session_project import (
    generate_project_session_name,
    ensure_project_session,
    send_to_developer_session,
    send_to_project_session,
    get_project_session_status,
    terminate_project_session,
    create_integrated_project_session,
)

from .ecosystem import (
    get_ecosystem_status,
    get_unified_status,
    create_integrated_session_flow,
    get_organization_session_status,
    verify_ecosystem_integration,
    verify_documentation_migration,
    get_legacy_api_deprecation_status,
    verify_final_integration_complete,
)

from .metrics import (
    get_communication_metrics,
    reset_metrics,
    verify_cross_session_connectivity,
    send_reliable_cross_session_message,
    measure_parallel_session_scalability,
)

from .session import (
    ensure_org_session_ready,
    get_session_architecture_2_performance,
    verify_complete_2_function_separation,
)

# Import session name directly from variables
from variables import get_session_name

# Export all public APIs
__all__ = [
    # Session management
    'get_session_name',
    'ensure_org_session_ready',
    'get_session_architecture_2_performance',
    'verify_complete_2_function_separation',
    
    # Developer management
    'start_developer',
    'send_command_to_developer_by_directory',
    'get_all_developers_status',
    'clean_dead_developers_from_state',
    
    # Designer management
    'start_designer',
    'send_command_to_designer',
    'send_to_designer_optimized',
    
    # History management
    'check_developer_has_history',
    'get_claude_history',
    
    # Project session management
    'generate_project_session_name',
    'ensure_project_session',
    'send_to_developer_session',
    'send_to_project_session',
    'get_project_session_status',
    'terminate_project_session',
    'create_integrated_project_session',
    
    # Organization session management
    'get_organization_session_status',
    
    # Ecosystem and status
    'get_ecosystem_status',
    'get_unified_status',
    'create_integrated_session_flow',
    
    # Cross-session communication
    'verify_cross_session_connectivity',
    'send_reliable_cross_session_message',
    
    # Metrics and monitoring
    'get_communication_metrics',
    'reset_metrics',
    'measure_parallel_session_scalability',
    
    # Migration and verification
    'verify_ecosystem_integration',
    'verify_documentation_migration',
    'get_legacy_api_deprecation_status',
    'verify_final_integration_complete',
]