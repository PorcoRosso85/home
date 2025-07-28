# ASVS Reference Management POC

A proof-of-concept implementation for managing external security standards (like OWASP ASVS) as reference entities in a graph database, enabling requirement traceability, compliance mapping, and quality guardrails.

## Purpose

This POC demonstrates how to leverage external security standards as a reference foundation for requirement management. It provides:

- **Reference Entity Management**: Store and query security standards (ASVS, NIST, etc.) as graph entities
- **Compliance Mapping**: Link requirements to reference standards for traceability
- **Quality Guardrails**: Enforce mandatory reference associations or justified exceptions
- **Workflow Enforcement**: State machine for requirement lifecycle with audit trails
- **Coverage Analysis**: Gap analysis and compliance reporting against standards

## Key Features

### 1. Reference Repository
- Graph-based storage for reference entities using KuzuDB
- CRUD operations for reference management
- Relationship tracking (IMPLEMENTS) between references
- Full-text search capabilities

### 2. Data Structure
- Standard → Chapter → Section → Requirement hierarchy
- Version management support
- Flexible search and filtering capabilities

### 3. Workflow Enforcement
- State machine: DRAFT → UNDER_REVIEW → APPROVED → IMPLEMENTING → IMPLEMENTED
- Transition validation with business rules
- Review comment system with severity levels
- Complete audit trail for all operations

### 4. ASVS Data Loader
- YAML-based ASVS data import
- Jinja2 template engine for Cypher query generation
- Batch loading of security standards
- Extensible for other standards (NIST, ISO, etc.)

## Architecture

### Main Modules

```
asvs_reference/
├── reference_repository.py      # Core repository with KuzuDB integration
├── enforced_workflow.py         # Workflow state machine and business rules
├── asvs_loader.py              # YAML data loader with template engine
├── data/                       # Sample ASVS and rule data
├── ddl/                        # Database schema definitions
├── templates/                  # Jinja2 templates for Cypher generation
└── e2e/                        # End-to-end integration tests
```

### Module Responsibilities

- **reference_repository.py**: Low-level database operations, error handling, connection management
- **reference_guardrails.py**: Reference-requirement mapping, gap analysis, compliance checking
- **enforced_workflow.py**: Business logic enforcement, state transitions, audit logging
- **asvs_loader.py**: Data import/export, template processing, batch operations

## Usage Examples

### Running Tests

```bash
# Run all tests
nix run .#test

# Run specific test file
python -m pytest test_reference_repository.py -v

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

### Running Demos

```bash
# Basic guardrails demo
nix run .#demo-guardrails

# Mandatory references enforcement demo
nix run .#demo-mandatory

# Enforced workflow demo
python demo_enforced_guardrails.py
```

### Using the CLI

```bash
# Load ASVS data from YAML
nix run .#cli

# Or directly
python asvs_loader.py
```

### Python API Examples

```python
# Create repository
from reference_repository import create_reference_repository

repo = create_reference_repository(":memory:")

# Save a reference
reference = {
    "uri": "ASVS:V2.1.1",
    "title": "Password Length",
    "entity_type": "security_control",
    "description": "Verify minimum password length of 12 characters"
}
repo["save"](reference)

# Create workflow with guardrails
from enforced_workflow import create_workflow_repository

workflow = create_workflow_repository()

# Create requirement with mandatory reference
requirement = {
    "id": "REQ-001",
    "title": "Implement password policy",
    "references": ["ASVS:V2.1.1"]  # Required!
}
result = workflow["create_requirement"](requirement)

# Or with justified exception
requirement_with_exception = {
    "id": "REQ-002",
    "title": "Custom authentication",
    "exception": {
        "type": "custom_implementation",
        "justification": "Using biometric authentication instead of passwords, which provides equivalent security through different means"
    }
}
```

## Dependencies

### Core Dependencies
- **kuzu_py**: Local KuzuDB Python wrapper (path: `../../persistence/kuzu_py`)
- **KuzuDB**: Graph database engine
- **PyYAML**: YAML data parsing
- **Jinja2**: Template engine for Cypher generation
- **pytest**: Testing framework

### Development Dependencies
- Black, isort, flake8: Code formatting and linting
- mypy: Type checking
- pytest-cov: Test coverage reporting

## Current Status

### Working Features
- ✅ Reference entity CRUD operations
- ✅ ASVS data loading from YAML
- ✅ Guardrails with mandatory reference enforcement
- ✅ Exception handling with justification
- ✅ Basic workflow state machine
- ✅ Audit trail logging
- ✅ Gap analysis and coverage reporting

### Known Issues
- ⚠️ Tests require proper kuzu_py package structure (import path adjustment needed)
- ⚠️ Schema initialization must be done manually or through environment variable
- ⚠️ Some tests use in-memory mock data instead of actual database

### Pending Improvements
- [ ] Full integration with requirement/graph system
- [ ] Advanced NLP for reference suggestions
- [ ] Multi-standard support (NIST, ISO)
- [ ] GraphQL API layer
- [ ] Web UI for compliance dashboard

## Development

### Setting up the environment

```bash
# Enter development shell
nix develop

# Install in editable mode (if using pip)
pip install -e .
```

### Running individual components

```python
# Test ASVS loader
from asvs_loader import ASVSLoader
loader = ASVSLoader()
cypher = loader.load_and_generate("asvs_sample.yaml")

# Test guardrails
from reference_guardrails import create_reference_repository
repo = create_reference_repository(":memory:")
repo["load_asvs_samples"]()
```

## Integration Points

This POC is designed to integrate with the larger requirement management system:

1. **Database Integration**: Uses same KuzuDB instance as requirement/graph
2. **Error Handling**: Consistent error types (ValidationError, NotFoundError, etc.)
3. **Workflow Alignment**: Compatible with existing requirement workflows
4. **Schema Compatibility**: DDL can be merged with main requirement schema

## Future Roadmap

1. **Phase 1**: Fix kuzu_py import issues, complete test coverage
2. **Phase 2**: Integrate with main requirement system
3. **Phase 3**: Add support for multiple standards (NIST, ISO)
4. **Phase 4**: Build compliance dashboard UI
5. **Phase 5**: Implement ML-based reference suggestions

## Contributing

When contributing to this POC:

1. Ensure all tests pass: `nix run .#test`
2. Follow the established patterns for error handling
3. Update tests for new features
4. Document any new business rules in docstrings
5. Use type hints for better code clarity

## License

MIT License (as specified in pyproject.toml)