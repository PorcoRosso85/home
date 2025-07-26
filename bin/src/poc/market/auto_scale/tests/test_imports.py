"""Test module imports to verify project structure."""

import pytest
import sys
from pathlib import Path


def test_module_structure_exists():
    """Test that the auto_scale_contract package exists."""
    try:
        import auto_scale_contract
        assert auto_scale_contract is not None
    except ImportError as e:
        pytest.fail(f"Failed to import auto_scale_contract: {e}")


def test_contract_management_module_imports():
    """Test that contract_management module can be imported."""
    try:
        from auto_scale_contract import contract_management
        assert contract_management is not None
    except ImportError as e:
        pytest.fail(f"Failed to import contract_management module: {e}")


def test_contract_management_submodules():
    """Test that contract_management submodules follow DDD structure."""
    expected_submodules = ["domain", "application", "infrastructure"]
    
    try:
        from auto_scale_contract import contract_management
        
        for submodule in expected_submodules:
            try:
                module = getattr(contract_management, submodule)
                assert module is not None, f"Submodule {submodule} is None"
            except AttributeError:
                pytest.fail(f"contract_management.{submodule} does not exist")
                
    except ImportError as e:
        pytest.fail(f"Failed to import contract_management for submodule test: {e}")


def test_domain_models_import():
    """Test that domain models can be imported."""
    try:
        from auto_scale_contract.contract_management.domain import (
            Contract,
            ContractRepository,
            ContractStatus,
            ContractId,
            Money,
        )
        
        # Verify imports are not None
        assert Contract is not None
        assert ContractRepository is not None
        assert ContractStatus is not None
        assert ContractId is not None
        assert Money is not None
        
    except ImportError as e:
        pytest.fail(f"Failed to import domain models: {e}")


def test_application_services_import():
    """Test that application services can be imported."""
    try:
        from auto_scale_contract.contract_management.application import (
            ContractService,
        )
        
        # Verify imports are not None
        assert ContractService is not None
        
    except ImportError as e:
        pytest.fail(f"Failed to import application services: {e}")


def test_infrastructure_repositories_import():
    """Test that infrastructure repositories can be imported."""
    try:
        from auto_scale_contract.contract_management.infrastructure import (
            ContractRepository,
        )
        
        # Verify imports are not None
        assert ContractRepository is not None
        
    except ImportError as e:
        pytest.fail(f"Failed to import infrastructure repositories: {e}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])