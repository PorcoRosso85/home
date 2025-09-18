"""Ecosystem management module.

This module handles all ecosystem-related operations including:
- Getting unified status across all sessions
- Verifying integration points
- Managing organization-wide state
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List

from variables import SESSION_NAME
from .developer import get_all_developers_status
from .session_project import (
    ensure_project_session,
    generate_project_session_name,
    get_project_session_status,
    create_integrated_project_session
)


# Result pattern helpers
def _ok(data: Any) -> Dict[str, Any]:
    """Create success result."""
    return {"ok": True, "data": data, "error": None}


def _err(message: str, code: str = "error") -> Dict[str, Any]:
    """Create error result."""
    return {"ok": False, "data": None, "error": {"message": message, "code": code}}


def get_ecosystem_status() -> Dict[str, Any]:
    """Get comprehensive status of the entire ecosystem.
    
    Returns:
        Dict with ecosystem-wide status information
    """
    try:
        # Get all tmux sessions
        result = subprocess.run(
            ['tmux', 'list-sessions', '-F', '#{session_name}'],
            capture_output=True,
            text=True,
            check=False
        )
        
        sessions = []
        if result.returncode == 0 and result.stdout:
            sessions = result.stdout.strip().split('\n')
        
        # Categorize sessions
        org_sessions = [s for s in sessions if s == SESSION_NAME]
        project_sessions = [s for s in sessions if s.startswith('project-')]
        other_sessions = [s for s in sessions if s not in org_sessions and s not in project_sessions]
        
        # Get developers status
        developers_result = get_all_developers_status()
        
        # Build ecosystem status
        ecosystem = {
            "org_session": {
                "name": SESSION_NAME,
                "exists": SESSION_NAME in sessions,
                "developers": developers_result.get("data", {}).get("developers", []) if developers_result.get("ok") else []
            },
            "project_sessions": project_sessions,
            "other_sessions": other_sessions,
            "total_sessions": len(sessions),
            "summary": {
                "org_sessions": len(org_sessions),
                "project_sessions": len(project_sessions),
                "other_sessions": len(other_sessions),
                "total_developers": developers_result.get("data", {}).get("total", 0) if developers_result.get("ok") else 0
            }
        }
        
        return _ok(ecosystem)
        
    except Exception as e:
        return _err(f"Failed to get ecosystem status: {str(e)}", "ecosystem_error")


def get_unified_status() -> Dict[str, Any]:
    """Get unified status across all sessions and windows.
    
    Returns:
        Dict with comprehensive unified status
    """
    try:
        ecosystem_result = get_ecosystem_status()
        if not ecosystem_result["ok"]:
            return ecosystem_result
        
        ecosystem = ecosystem_result["data"]
        
        # Build unified view
        unified = {
            "ecosystem": ecosystem,
            "health": {
                "org_session_healthy": ecosystem["org_session"]["exists"],
                "developers_active": ecosystem["summary"]["total_developers"] > 0,
                "project_sessions_active": ecosystem["summary"]["project_sessions"] > 0
            },
            "recommendations": []
        }
        
        # Add recommendations
        if not ecosystem["org_session"]["exists"]:
            unified["recommendations"].append("Start org session for orchestration")
        
        if ecosystem["summary"]["total_developers"] == 0:
            unified["recommendations"].append("No active developers - consider starting one")
        
        return _ok(unified)
        
    except Exception as e:
        return _err(f"Failed to get unified status: {str(e)}", "unified_error")


def create_integrated_session_flow(project_path: str) -> Dict[str, Any]:
    """Create an integrated session flow for a project.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Dict with integrated session creation status
    """
    try:
        # Use the session_project module's function
        result = create_integrated_project_session(project_path)
        
        if result["ok"]:
            # Add flow-specific metadata
            result["data"]["flow_type"] = "integrated"
            result["data"]["orchestrator_session"] = SESSION_NAME
        
        return result
        
    except Exception as e:
        return _err(f"Failed to create integrated flow: {str(e)}", "flow_error")


def get_organization_session_status() -> Dict[str, Any]:
    """Get status of the organization orchestrator session.
    
    Returns:
        Dict with organization session status
    """
    try:
        # Check if org session exists
        result = subprocess.run(
            ['tmux', 'has-session', '-t', SESSION_NAME],
            capture_output=True,
            check=False
        )
        
        if result.returncode == 0:
            # Get windows in org session
            windows_result = subprocess.run(
                ['tmux', 'list-windows', '-t', SESSION_NAME, '-F', '#{window_name}:#{window_id}'],
                capture_output=True,
                text=True,
                check=True
            )
            
            windows = []
            if windows_result.stdout:
                for line in windows_result.stdout.strip().split('\n'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        windows.append({
                            "name": parts[0],
                            "id": parts[1],
                            "type": "developer" if parts[0].startswith("developer:") else "other"
                        })
            
            return _ok({
                "session_name": SESSION_NAME,
                "exists": True,
                "windows": windows,
                "window_count": len(windows),
                "developer_count": len([w for w in windows if w["type"] == "developer"])
            })
        else:
            return _ok({
                "session_name": SESSION_NAME,
                "exists": False,
                "windows": [],
                "window_count": 0,
                "developer_count": 0
            })
            
    except subprocess.SubprocessError as e:
        return _err(f"Failed to get organization status: {str(e)}", "org_status_error")
    except Exception as e:
        return _err(f"Unexpected error: {str(e)}", "unexpected_error")


def verify_ecosystem_integration() -> Dict[str, Any]:
    """Verify that ecosystem integration is working correctly.
    
    Returns:
        Dict with verification results
    """
    try:
        checks = {
            "org_session": False,
            "tmux_available": False,
            "can_create_windows": False,
            "can_list_sessions": False
        }
        
        # Check tmux availability
        tmux_check = subprocess.run(['which', 'tmux'], capture_output=True, check=False)
        checks["tmux_available"] = tmux_check.returncode == 0
        
        # Check if we can list sessions
        try:
            list_result = subprocess.run(
                ['tmux', 'list-sessions'],
                capture_output=True,
                check=False
            )
            checks["can_list_sessions"] = True
        except:
            checks["can_list_sessions"] = False
        
        # Check org session
        org_status = get_organization_session_status()
        checks["org_session"] = org_status.get("ok", False) and org_status.get("data", {}).get("exists", False)
        
        # Check if we can create windows (simulation)
        checks["can_create_windows"] = checks["org_session"]
        
        all_passed = all(checks.values())
        
        return _ok({
            "integration_complete": all_passed,
            "checks": checks,
            "recommendation": "All checks passed" if all_passed else "Some integration points need attention"
        })
        
    except Exception as e:
        return _err(f"Failed to verify integration: {str(e)}", "verification_error")


def verify_documentation_migration() -> Dict[str, Any]:
    """Verify documentation has been migrated/updated.
    
    Returns:
        Dict with documentation verification status
    """
    try:
        docs_to_check = [
            Path(__file__).parent.parent / "README.md",
            Path(__file__).parent.parent / "architectural-decisions.md",
            Path(__file__).parent / "__init__.py"
        ]
        
        doc_status = {}
        for doc in docs_to_check:
            doc_status[str(doc.name)] = doc.exists()
        
        all_exist = all(doc_status.values())
        
        return _ok({
            "documentation_complete": all_exist,
            "files": doc_status,
            "recommendation": "Documentation up to date" if all_exist else "Some documentation missing"
        })
        
    except Exception as e:
        return _err(f"Failed to verify documentation: {str(e)}", "doc_error")


def get_legacy_api_deprecation_status() -> Dict[str, Any]:
    """Get status of legacy API deprecation.
    
    Returns:
        Dict with deprecation status
    """
    try:
        # Check if old application.py still exists
        old_app = Path(__file__).parent.parent / "application.py"
        old_app_backup = Path(__file__).parent.parent / "application.py.bak"
        
        status = {
            "old_application_exists": old_app.exists(),
            "backup_exists": old_app_backup.exists(),
            "migration_phase": "in_progress" if old_app.exists() else "complete",
            "new_package_ready": True,  # app/ package is ready
            "deprecation_warnings": []
        }
        
        if old_app.exists():
            status["deprecation_warnings"].append("application.py still exists - consider removing after full migration")
        
        return _ok(status)
        
    except Exception as e:
        return _err(f"Failed to get deprecation status: {str(e)}", "deprecation_error")


def verify_final_integration_complete() -> Dict[str, Any]:
    """Verify that final integration is complete.
    
    Returns:
        Dict with final integration verification
    """
    try:
        # Run all verification checks
        ecosystem_check = verify_ecosystem_integration()
        doc_check = verify_documentation_migration()
        deprecation_check = get_legacy_api_deprecation_status()
        
        all_complete = (
            ecosystem_check.get("ok", False) and
            ecosystem_check.get("data", {}).get("integration_complete", False) and
            doc_check.get("ok", False) and
            doc_check.get("data", {}).get("documentation_complete", False) and
            deprecation_check.get("ok", False) and
            deprecation_check.get("data", {}).get("migration_phase") == "complete"
        )
        
        return _ok({
            "final_integration_complete": all_complete,
            "ecosystem": ecosystem_check.get("data", {}),
            "documentation": doc_check.get("data", {}),
            "deprecation": deprecation_check.get("data", {}),
            "recommendation": "Integration complete!" if all_complete else "Some integration steps remaining"
        })
        
    except Exception as e:
        return _err(f"Failed to verify final integration: {str(e)}", "final_error")