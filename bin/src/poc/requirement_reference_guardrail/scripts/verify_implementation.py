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

def test_security_detection():
    """Test security category detection."""
    print("Testing security category detection...")
    
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
            print(f"  ✓ '{description}' -> {result}")
            passed += 1
        else:
            print(f"  ✗ '{description}' -> {result} (expected: {expected})")
    
    print(f"\nPassed: {passed}/{len(tests)}")
    return passed == len(tests)

def test_reference_compliance():
    """Test reference compliance checking."""
    print("\nTesting reference compliance...")
    
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
            print(f"  ✓ {category} with {refs} -> {'compliant' if is_compliant else 'non-compliant'}")
            passed += 1
        else:
            print(f"  ✗ {category} with {refs} -> {'compliant' if is_compliant else 'non-compliant'} (expected: {'compliant' if should_pass else 'non-compliant'})")
            if error:
                print(f"    Error: {error}")
    
    print(f"\nPassed: {passed}/{len(tests)}")
    return passed == len(tests)

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Requirement Reference Guardrail Implementation Verification")
    print("=" * 60)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_security_detection()
    all_passed &= test_reference_compliance()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! Implementation is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())