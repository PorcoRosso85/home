#!/usr/bin/env python3
"""
Simple test runner for RGL issues
"""
import sys
sys.path.append('/home/nixos/bin/src/requirement/graph')

from test_rgl_issues import (
    TestFrictionDetectionIssues,
    TestContradictionDetectionIssues, 
    TestFeedbackUsabilityIssues
)

def run_test_class(test_class, class_name):
    """Run all test methods in a test class"""
    print(f"\n{class_name}:")
    instance = test_class()
    passed = 0
    failed = 0
    
    for method_name in dir(instance):
        if method_name.startswith('test_'):
            method = getattr(instance, method_name)
            try:
                method()
                print(f"  ✓ {method_name}")
                passed += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {str(e)}")
                failed += 1
    
    return passed, failed

if __name__ == "__main__":
    total_passed = 0
    total_failed = 0
    
    # Run tests
    passed, failed = run_test_class(TestFrictionDetectionIssues, "TestFrictionDetectionIssues")
    total_passed += passed
    total_failed += failed
    
    passed, failed = run_test_class(TestContradictionDetectionIssues, "TestContradictionDetectionIssues")
    total_passed += passed
    total_failed += failed
    
    passed, failed = run_test_class(TestFeedbackUsabilityIssues, "TestFeedbackUsabilityIssues")
    total_passed += passed
    total_failed += failed
    
    print(f"\n{'='*50}")
    print(f"Total: {total_passed} passed, {total_failed} failed")
    
    sys.exit(0 if total_failed == 0 else 1)