#!/usr/bin/env python3
"""
Demo script showing the guardrail logic without database dependencies.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from guardrail.guardrail_logic import (
    detect_security_category,
    check_reference_compliance,
    SECURITY_CATEGORIES
)


def main():
    """Demonstrate guardrail logic"""
    print("Requirement Reference Guardrail Logic Demo")
    print("=" * 60)
    
    # Test requirements
    test_requirements = [
        {
            "id": "REQ-001",
            "description": "Display user dashboard with recent activity",
            "references": []
        },
        {
            "id": "REQ-002",
            "description": "Implement secure user authentication with password hashing",
            "references": ["ASVS-V2.1.1"]
        },
        {
            "id": "REQ-003",
            "description": "Add login functionality with secure session management",
            "references": ["ASVS-V4.1.1"]  # Wrong reference for authentication
        },
        {
            "id": "REQ-004",
            "description": "Implement role-based access control for admin panel",
            "references": []
        },
        {
            "id": "REQ-005",
            "description": "Encrypt sensitive data at rest using AES-256",
            "references": ["ASVS-V6.2.1"]
        },
        {
            "id": "REQ-006",
            "description": "Validate and sanitize all user input to prevent XSS",
            "references": ["ASVS-V5.3.3", "NIST-SI-10"]
        }
    ]
    
    print("\nAnalyzing requirements for security compliance:\n")
    
    for req in test_requirements:
        req_id = req["id"]
        description = req["description"]
        references = req["references"]
        
        print(f"{req_id}: {description}")
        
        # Detect security category
        category = detect_security_category(description)
        
        if category is None:
            print(f"  ✓ Non-security requirement - no references required")
            print(f"  Status: ALLOWED\n")
        else:
            print(f"  → Security category detected: {category}")
            
            # Check reference compliance
            is_compliant, error_msg = check_reference_compliance(category, references)
            
            if is_compliant:
                print(f"  ✓ References compliant: {', '.join(references)}")
                print(f"  Status: ALLOWED\n")
            else:
                print(f"  ✗ References non-compliant")
                print(f"  Error: {error_msg}")
                print(f"  Provided references: {', '.join(references) if references else 'None'}")
                print(f"  Status: BLOCKED\n")
    
    # Show security categories and their requirements
    print("\n" + "=" * 60)
    print("Security Categories and Required References:")
    print("=" * 60)
    
    for category, config in SECURITY_CATEGORIES.items():
        print(f"\n{category.upper()}:")
        print(f"  Keywords: {', '.join(sorted(config['keywords']))}")
        print(f"  Required patterns: {', '.join(config['required_references'])}")
        print(f"  Message: {config['message']}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("- Non-security requirements can be created without references")
    print("- Security requirements MUST have appropriate references")
    print("- References are checked against category-specific patterns")
    print("- Failed requirements would need exception requests")


if __name__ == "__main__":
    main()