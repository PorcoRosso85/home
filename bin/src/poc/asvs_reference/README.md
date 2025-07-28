# ASVS Reference Management POC

A proof-of-concept implementation for managing external security standards (like OWASP ASVS) as reference entities in a graph database, enabling requirement traceability, compliance mapping, and quality guardrails.

## Purpose

This POC provides a clean data provider interface for OWASP ASVS (Application Security Verification Standard) data. It serves as a reference data source for other POCs that need to access security requirements.

### What it provides:
- **ASVS Data Management**: Store and query ASVS requirements in a graph database
- **Type-Safe API**: Strongly typed interfaces using TypedDict
- **Search Capabilities**: Find requirements by number, keyword, level, or section
- **Version Support**: Manage multiple ASVS versions (currently 4.0.3 and 5.0)

### Previous Functionality (Removed)
This POC previously included guardrail enforcement functionality that has been removed to achieve better separation of concerns. The specifications for these features are preserved in:
- `GUARDRAIL_SPECS_MIGRATION.md` - Complete migration guide for implementing guardrails elsewhere
- `data/guardrail_test_specs.yaml` - Test specifications in structured format

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

### 3. ASVS Data Loader
- YAML-based ASVS data import
- Jinja2 template engine for Cypher query generation
- Batch loading of security standards
- Extensible for other standards (NIST, ISO, etc.)

## Architecture

### Main Modules

```
asvs_reference/
├── asvs_types.py               # Type definitions for ASVS data structures
├── asvs_api.py                 # Data provider API for other POCs
├── reference_repository.py      # Core repository with KuzuDB integration
├── asvs_loader.py              # YAML data loader with template engine
├── asvs_direct_import.py       # Direct import from Markdown to KuzuDB
├── data/                       # Sample ASVS and rule data
├── ddl/                        # Database schema definitions
├── templates/                  # Jinja2 templates for Cypher generation
└── e2e/                        # End-to-end integration tests
```

### Module Responsibilities

- **asvs_types.py**: Type definitions for all ASVS data structures
- **asvs_api.py**: High-level API for other POCs to access ASVS data
- **reference_repository.py**: Low-level database operations, error handling, connection management
- **asvs_loader.py**: Data import/export, template processing, batch operations
- **asvs_direct_import.py**: Direct Markdown to database import without YAML

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

### Loading ASVS Data

```bash
# Fetch ASVS 5.0 data from GitHub
nix run .#fetch-asvs5

# Or load from local YAML file
python asvs_loader.py

# Direct import from Markdown
python scripts/asvs_direct_import.py path/to/asvs.md
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
# Using the ASVS Data Provider API
from asvs_api import create_asvs_provider

# Create provider
provider = create_asvs_provider(":memory:")

# Get a specific requirement
response = provider.get_requirement_by_number("2.1.1")
if response['type'] == 'Success':
    req = response['value']
    print(f"{req['number']}: {req['description']}")

# Search requirements
from asvs_types import SearchFilter
filter: SearchFilter = {'keyword': 'password', 'levels': {'level1': True}}
response = provider.search_requirements(filter)
if response['type'] == 'Success':
    result = response['value']
    print(f"Found {result['total_count']} requirements")
    for req in result['requirements']:
        print(f"  - {req['number']}: {req['description']}")

# Get all Level 1 requirements
response = provider.get_requirements_by_level(1)

# Get requirements by section
response = provider.get_requirements_by_section("2.1")
```

### Lower-level Repository API

```python
# Create repository directly
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
- ⚠️ Guardrail specifications removed - see `GUARDRAIL_SPECS_MIGRATION.md` for implementation in other POCs

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