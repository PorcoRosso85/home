"""Type definitions for contract_e2e framework"""

from typing import TypedDict, Dict, Any, List, Union, Literal


class ProcessError(TypedDict):
    """Process execution error"""
    type: Literal["process_error"]
    exit_code: int
    stderr: str
    timeout: bool


class ValidationError(TypedDict):
    """Schema validation error"""
    type: Literal["validation_error"]
    schema_path: str
    instance_path: str
    message: str


class ParseError(TypedDict):
    """JSON parse error"""
    type: Literal["parse_error"]
    output: str
    error: str


ErrorType = Union[ProcessError, ValidationError, ParseError]


class TestCase(TypedDict):
    """Test case result"""
    input: Dict[str, Any]
    status: Literal["passed", "failed"]
    stdout: str
    stderr: str
    returncode: int
    output: Dict[str, Any]  # Optional - only when JSON parsing succeeds
    error: str  # Optional - only when failed


class TestReport(TypedDict):
    """Test execution report"""
    passed: int
    failed: int


class SuccessResult(TypedDict):
    """Successful test result"""
    ok: Literal[True]
    report: TestReport
    test_cases: List[TestCase]


class ErrorResult(TypedDict):
    """Error result"""
    ok: Literal[False]
    error: ErrorType
    report: TestReport
    test_cases: List[TestCase]


TestResult = Union[SuccessResult, ErrorResult]