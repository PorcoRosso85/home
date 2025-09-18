"""
E2E Internal Test Configuration
Imports shared fixtures from root conftest.py and provides E2E-specific fixtures
"""
import sys
import os
from pathlib import Path

# Add the root directory to Python path to import root conftest
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Import shared fixtures from root conftest.py
from conftest import (
    run_system_optimized,
    inmemory_db,
    file_db,
    run_system,
    perf_collector,
    measure
)

# Re-export imported fixtures so pytest can discover them
__all__ = [
    'run_system_optimized',
    'inmemory_db', 
    'file_db',
    'run_system',
    'perf_collector',
    'measure'
]

# E2E-specific fixtures can be added below
import pytest
import tempfile
from typing import Dict, Any, List


@pytest.fixture
def e2e_sample_requirements():
    """Sample requirements for E2E testing"""
    return [
        {
            "req_id": "req_001",
            "description": "System shall support user authentication",
            "tags": ["security", "authentication"]
        },
        {
            "req_id": "req_002", 
            "description": "System shall log all access attempts",
            "tags": ["security", "logging"]
        },
        {
            "req_id": "req_003",
            "description": "System shall encrypt sensitive data",
            "tags": ["security", "encryption"]
        }
    ]


@pytest.fixture
def e2e_test_graph(inmemory_db, run_system):
    """
    Creates a test graph with sample requirements and dependencies
    Uses inmemory_db for isolation
    """
    # Add sample requirements
    requirements = [
        {"req_id": "auth_001", "description": "Basic authentication"},
        {"req_id": "auth_002", "description": "Two-factor authentication"},
        {"req_id": "db_001", "description": "User database"}
    ]
    
    for req in requirements:
        result = run_system({
            "type": "requirement",
            "action": "add",
            **req
        }, inmemory_db)
        
        if "error" in result:
            pytest.fail(f"Failed to add requirement {req['req_id']}: {result}")
    
    # Add dependencies
    dependencies = [
        ("auth_001", "db_001"),
        ("auth_002", "auth_001")
    ]
    
    for dependent, dependency in dependencies:
        result = run_system({
            "type": "dependency",
            "action": "add",
            "dependent_req_id": dependent,
            "dependency_req_id": dependency
        }, inmemory_db)
        
        if "error" in result:
            pytest.fail(f"Failed to add dependency {dependent}->{dependency}: {result}")
    
    return inmemory_db


@pytest.fixture
def e2e_batch_runner(run_system):
    """
    Helper fixture for running multiple operations in sequence
    Useful for E2E test scenarios
    """
    def run_batch(operations: List[Dict[str, Any]], db_path: str) -> List[Dict[str, Any]]:
        results = []
        for op in operations:
            result = run_system(op, db_path)
            results.append(result)
            # Stop on first error
            if "error" in result:
                break
        return results
    
    return run_batch


@pytest.fixture(scope="session")
def e2e_performance_thresholds():
    """
    E2E-specific performance thresholds
    Can be overridden by environment variables
    """
    return {
        "requirement_add": float(os.environ.get("E2E_THRESHOLD_REQ_ADD", "0.5")),
        "dependency_add": float(os.environ.get("E2E_THRESHOLD_DEP_ADD", "0.5")),
        "search": float(os.environ.get("E2E_THRESHOLD_SEARCH", "1.0")),
        "graph_analysis": float(os.environ.get("E2E_THRESHOLD_ANALYSIS", "2.0")),
        "bulk_operation": float(os.environ.get("E2E_THRESHOLD_BULK", "5.0"))
    }