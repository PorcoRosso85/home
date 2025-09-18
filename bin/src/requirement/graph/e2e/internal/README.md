# Internal E2E Tests

This directory contains end-to-end tests that verify the complete requirement graph system functionality.

## Purpose

Internal E2E tests validate the full application flow within this module:
- Requirement creation, versioning, and querying
- Dependency management and validation
- Search functionality integration
- Template processing and error handling

## Test Coverage

Tests in this directory cover:
1. **Complete User Journeys**: Creating requirements with dependencies
2. **Integration Points**: Database operations, search adapter, template processor
3. **Error Scenarios**: Validation failures, circular dependencies, constraint violations
4. **Performance**: Query execution time and memory usage under load

## Running Tests

```bash
pytest e2e/internal/
```

## Structure

- `test_*.py`: Individual E2E test modules
- Test fixtures and utilities are shared with parent test infrastructure