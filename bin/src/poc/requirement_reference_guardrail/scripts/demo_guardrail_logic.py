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
from log_py import log


def main():
    """Demonstrate guardrail logic"""
    log("info", {"message": "Starting Requirement Reference Guardrail Logic Demo"})
    log("info", {"message": "=" * 60})
    
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
    
    log("info", {"message": "Analyzing requirements for security compliance"})
    
    for req in test_requirements:
        req_id = req["id"]
        description = req["description"]
        references = req["references"]
        
        log("info", {"message": f"Analyzing requirement", "req_id": req_id, "description": description})
        
        # Detect security category
        category = detect_security_category(description)
        
        if category is None:
            log("info", {"message": "Non-security requirement - no references required", "req_id": req_id, "status": "ALLOWED"})
        else:
            log("info", {"message": "Security category detected", "req_id": req_id, "category": category})
            
            # Check reference compliance
            is_compliant, error_msg = check_reference_compliance(category, references)
            
            if is_compliant:
                log("info", {
                    "message": "References compliant",
                    "req_id": req_id,
                    "references": references,
                    "status": "ALLOWED"
                })
            else:
                log("error", {
                    "message": "References non-compliant",
                    "req_id": req_id,
                    "error": error_msg,
                    "provided_references": references if references else [],
                    "status": "BLOCKED"
                })
    
    # Show security categories and their requirements
    log("info", {"message": "=" * 60})
    log("info", {"message": "Security Categories and Required References:"})
    log("info", {"message": "=" * 60})
    
    for category, config in SECURITY_CATEGORIES.items():
        log("info", {
            "message": f"Security category: {category.upper()}",
            "keywords": sorted(config['keywords']),
            "required_patterns": config['required_references'],
            "category_message": config['message']
        })
    
    log("info", {"message": "=" * 60})
    log("info", {
        "message": "Summary:",
        "rules": [
            "Non-security requirements can be created without references",
            "Security requirements MUST have appropriate references",
            "References are checked against category-specific patterns",
            "Failed requirements would need exception requests"
        ]
    })


if __name__ == "__main__":
    main()