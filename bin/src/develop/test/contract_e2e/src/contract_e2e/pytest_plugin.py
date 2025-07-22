"""pytest plugin for contract-based E2E testing"""

import pytest
import json
from pathlib import Path
from .core import generate_sample_from_schema
from .runner import run_contract_tests


def pytest_addoption(parser):
    """Add contract testing options to pytest"""
    group = parser.getgroup("contract")
    group.addoption(
        "--contract-test",
        action="store",
        help="Executable to test with contract testing"
    )
    group.addoption(
        "--input-schema",
        action="store",
        help="Path to input JSON schema"
    )
    group.addoption(
        "--output-schema",
        action="store",
        help="Path to output JSON schema"
    )
    group.addoption(
        "--contract-test-count",
        action="store",
        type=int,
        default=100,
        help="Number of test cases to generate"
    )


@pytest.fixture
def contract_test_config(request):
    """Fixture providing contract test configuration"""
    return {
        "executable": request.config.getoption("--contract-test"),
        "input_schema": request.config.getoption("--input-schema"),
        "output_schema": request.config.getoption("--output-schema"),
        "test_count": request.config.getoption("--contract-test-count"),
    }


def contract_test(input_schema, output_schema, executable=None, test_count=100):
    """Decorator for contract-based tests"""
    def decorator(test_func):
        @pytest.mark.parametrize("test_case", range(test_count))
        def wrapper(test_case, contract_test_config):
            # Load schemas
            with open(input_schema) as f:
                input_schema_data = json.load(f)
            with open(output_schema) as f:
                output_schema_data = json.load(f)
            
            # Use executable from decorator or command line
            exec_path = executable or contract_test_config["executable"]
            
            # Run contract test
            result = run_contract_tests(
                executable=exec_path,
                input_schema=input_schema_data,
                output_schema=output_schema_data,
                test_count=1
            )
            
            assert result["ok"], f"Contract test failed: {result}"
            
        return wrapper
    return decorator


# pytest plugin entry point
pytest_plugins = ["contract_e2e.pytest_plugin"]