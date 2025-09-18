# Minimal Guardrail Enforcer Implementation

## Overview

Created a minimal implementation of requirement reference guardrails with hardcoded basic enforcement rules. This implementation can be later replaced with GuardrailRule nodes stored in the database.

## Files Created

### 1. `/src/guardrail/minimal_enforcer.py`
Main enforcement module with the following functions:

- **`enforce_basic_guardrails()`**: Creates requirements with reference validation in a transaction
- **`create_exception_request()`**: Creates exception requests for non-compliant requirements
- **`detect_security_category()`**: Detects if a requirement is security-related based on keywords
- **`check_reference_compliance()`**: Validates references against category requirements

### 2. `/src/guardrail/guardrail_logic.py`
Core logic module without database dependencies, containing:

- Security keyword definitions
- Security category configurations
- Detection and compliance checking logic

### 3. `/scripts/demo_guardrail_logic.py`
Demonstration script showing how the guardrail logic works without database dependencies.

### 4. `/scripts/example_enforcement.py`
Full example with database operations (requires KuzuDB).

### 5. `/tests/test_minimal_enforcer.py`
Comprehensive test suite covering all functionality.

## Key Features

### 1. Security Category Detection
The system detects five main security categories:
- **Authentication**: login, password, credential keywords
- **Authorization**: access control, permission, role keywords
- **Session Management**: session, token, JWT keywords
- **Cryptography**: encryption, cipher, hash keywords
- **Input Validation**: sanitize, validate, XSS keywords

### 2. Reference Compliance Rules
Each security category has required reference patterns:
- Authentication → ASVS-V2 or NIST-IA
- Authorization → ASVS-V4 or NIST-AC
- Session Management → ASVS-V3 or NIST-SC
- Cryptography → ASVS-V6 or NIST-SC
- Input Validation → ASVS-V5 or NIST-SI

### 3. Transaction Safety
All database operations are wrapped in transactions:
- Requirement creation and reference linking are atomic
- Rollback on any error ensures consistency

### 4. Exception Handling
Requirements that cannot meet guardrails can request exceptions:
- Exception requests track reason and mitigation
- Linked to requirements via HAS_EXCEPTION relationship

## Usage Example

```python
from guardrail import detect_security_category, check_reference_compliance

# Detect category
category = detect_security_category("Implement user authentication")
# Returns: "authentication"

# Check compliance
is_compliant, error = check_reference_compliance(
    "authentication", 
    ["ASVS-V2.1.1"]
)
# Returns: (True, None)

# With database connection
from guardrail.minimal_enforcer import enforce_basic_guardrails

result = enforce_basic_guardrails(
    conn,
    "REQ-001",
    "Implement secure login",
    ["ASVS-V2.1.1"]
)
# Returns: {"success": True, "requirement_created": True, ...}
```

## Design Decisions

1. **Hardcoded Rules**: Security categories and patterns are hardcoded for simplicity
2. **Modular Design**: Core logic separated from database operations
3. **Extensible**: Can easily add new categories or modify rules
4. **Transaction-Safe**: All database operations are atomic
5. **Clear Error Messages**: Specific guidance on what references are needed

## Future Enhancement Path

This minimal implementation can be replaced with database-driven rules:

1. Create GuardrailRule nodes in the database
2. Replace hardcoded `SECURITY_CATEGORIES` with database queries
3. Allow dynamic rule updates without code changes
4. Add more sophisticated pattern matching
5. Support custom organization-specific rules

## Testing

Run the demo without database:
```bash
nix-shell -p python312 --run "PYTHONPATH=./src python scripts/demo_guardrail_logic.py"
```

The implementation successfully demonstrates:
- Security requirement detection
- Reference validation
- Clear error messages for non-compliance
- Transaction-safe database operations