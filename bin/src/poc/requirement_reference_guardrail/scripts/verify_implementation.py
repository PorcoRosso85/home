#!/usr/bin/env python3
"""
Verify implementation by running key guardrail logic tests without pytest.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from guardrail.guardrail_logic import (
    detect_security_category,
    check_reference_compliance,
)
from log_py import log

def test_security_detection():
    """Test security category detection."""
    log("info", {"message": "Testing security category detection"})
    
    tests = [
        ("Implement user login", "authentication"),
        ("Add password reset", "authentication"),
        ("Control access to resources", "authorization"),
        ("Manage user sessions", "session_management"),
        ("Encrypt data at rest", "cryptography"),
        ("Validate user input", "input_validation"),
        ("Display dashboard", None),
    ]
    
    passed = 0
    for description, expected in tests:
        result = detect_security_category(description)
        if result == expected:
            log("info", {
                "message": "Test passed",
                "test": "security_detection",
                "description": description,
                "result": result,
                "status": "passed"
            })
            passed += 1
        else:
            log("error", {
                "message": "Test failed",
                "test": "security_detection",
                "description": description,
                "result": result,
                "expected": expected,
                "status": "failed"
            })
    
    log("info", {
        "message": "Security detection test summary",
        "passed": passed,
        "total": len(tests),
        "success_rate": f"{passed}/{len(tests)}"
    })
    return passed == len(tests)

def test_reference_compliance():
    """Test reference compliance checking."""
    log("info", {"message": "Testing reference compliance"})
    
    tests = [
        ("authentication", ["ASVS-V2.1.1"], True),
        ("authentication", ["ASVS-V4.1.1"], False),
        ("authorization", ["ASVS-V4.2.1"], True),
        ("authorization", ["NIST-AC-2"], True),
        ("cryptography", ["ASVS-V6.1.1"], True),
        ("cryptography", [], False),
    ]
    
    passed = 0
    for category, refs, should_pass in tests:
        is_compliant, error = check_reference_compliance(category, refs)
        if is_compliant == should_pass:
            log("info", {
                "message": "Test passed",
                "test": "reference_compliance",
                "category": category,
                "references": refs,
                "is_compliant": is_compliant,
                "status": "passed"
            })
            passed += 1
        else:
            log("error", {
                "message": "Test failed",
                "test": "reference_compliance",
                "category": category,
                "references": refs,
                "is_compliant": is_compliant,
                "expected_compliant": should_pass,
                "error": error,
                "status": "failed"
            })
    
    log("info", {
        "message": "Reference compliance test summary",
        "passed": passed,
        "total": len(tests),
        "success_rate": f"{passed}/{len(tests)}"
    })
    return passed == len(tests)

def main():
    """Run all verification tests."""
    log("info", {"message": "=" * 60})
    log("info", {"message": "Requirement Reference Guardrail Implementation Verification"})
    log("info", {"message": "=" * 60})
    
    all_passed = True
    
    # Run tests
    all_passed &= test_security_detection()
    all_passed &= test_reference_compliance()
    
    log("info", {"message": "=" * 60})
    if all_passed:
        log("info", {"message": "All tests passed! Implementation is working correctly.", "status": "success"})
        return 0
    else:
        log("error", {"message": "Some tests failed. Please check the implementation.", "status": "failure"})
        return 1

if __name__ == "__main__":
    sys.exit(main())