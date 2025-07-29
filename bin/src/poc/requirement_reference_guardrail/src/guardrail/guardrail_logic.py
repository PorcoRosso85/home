"""
Guardrail logic without database dependencies.

This module contains the core logic for requirement reference validation
that can be used independently of the database implementation.
"""
from typing import Dict, List, Optional, Tuple, Any


# Hardcoded security-related keywords for categorization
SECURITY_KEYWORDS = {
    "authentication", "auth", "login", "password", "credential",
    "authorization", "access control", "permission", "role",
    "security", "secure", "vulnerability", "threat", "risk",
    "encryption", "crypto", "cryptography", "cipher", "hash",
    "session", "token", "jwt", "oauth", "saml",
    "injection", "xss", "csrf", "sqli", "xxe",
    "sanitize", "validate", "escape", "filter",
    "audit", "logging", "monitoring", "compliance"
}

# Hardcoded security categories and their required reference patterns
SECURITY_CATEGORIES = {
    "authentication": {
        "keywords": {"auth", "login", "password", "credential", "identity"},
        "required_references": ["ASVS-V2", "NIST-IA"],
        "message": "Authentication requirements must reference ASVS V2 (Authentication) or NIST IA controls"
    },
    "authorization": {
        "keywords": {"authorization", "access control", "permission", "role", "rbac", "access"},
        "required_references": ["ASVS-V4", "NIST-AC"],
        "message": "Authorization requirements must reference ASVS V4 (Access Control) or NIST AC controls"
    },
    "session_management": {
        "keywords": {"session", "token", "jwt", "cookie", "logout"},
        "required_references": ["ASVS-V3", "NIST-SC"],
        "message": "Session management requirements must reference ASVS V3 (Session Management) or NIST SC controls"
    },
    "cryptography": {
        "keywords": {"encryption", "crypto", "cipher", "hash", "tls", "ssl", "encrypt"},
        "required_references": ["ASVS-V6", "NIST-SC"],
        "message": "Cryptography requirements must reference ASVS V6 (Cryptography) or NIST SC controls"
    },
    "input_validation": {
        "keywords": {"validation", "sanitize", "escape", "filter", "injection", "xss", "validate"},
        "required_references": ["ASVS-V5", "NIST-SI"],
        "message": "Input validation requirements must reference ASVS V5 (Validation) or NIST SI controls"
    }
}


def detect_security_category(description: str) -> Optional[str]:
    """
    Detect the security category of a requirement based on its description.
    
    Args:
        description: The requirement description text
        
    Returns:
        The detected category name or None if not security-related
    """
    description_lower = description.lower()
    
    # Check each category's keywords
    for category, config in SECURITY_CATEGORIES.items():
        if any(keyword in description_lower for keyword in config["keywords"]):
            return category
    
    # Check if it's generally security-related but doesn't fit a specific category
    if any(keyword in description_lower for keyword in SECURITY_KEYWORDS):
        return "general_security"
    
    return None


def check_reference_compliance(
    category: str,
    reference_ids: List[str]
) -> Tuple[bool, Optional[str]]:
    """
    Check if the provided references comply with the category requirements.
    
    Args:
        category: The security category
        reference_ids: List of reference entity IDs
        
    Returns:
        Tuple of (is_compliant, error_message)
    """
    if category not in SECURITY_CATEGORIES:
        # General security or unknown category - allow any security reference
        if not reference_ids:
            return False, "Security-related requirements must have at least one reference"
        return True, None
    
    config = SECURITY_CATEGORIES[category]
    required_patterns = config["required_references"]
    
    # Check if any reference matches the required patterns
    has_valid_reference = False
    for ref_id in reference_ids:
        for pattern in required_patterns:
            if ref_id.startswith(pattern):
                has_valid_reference = True
                break
        if has_valid_reference:
            break
    
    if not has_valid_reference:
        return False, config["message"]
    
    return True, None