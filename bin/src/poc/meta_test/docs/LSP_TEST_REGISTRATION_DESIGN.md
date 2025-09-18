# LSP-Based Test Registration Design

## Overview

Instead of file-scanning approaches, this design uses Language Server Protocol (LSP) for test discovery and registration. This provides real-time, accurate test information without the overhead of constant file scanning.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│   LSP Client    │────▶│   LSP Server     │────▶│  Meta-Test DB   │
│  (Editor/IDE)   │     │  (Test Analyzer) │     │   (KuzuDB)      │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         │ Test locations        │ Parse & analyze        │ Store
         │ & metadata           │ test structure         │ results
         ▼                       ▼                         ▼
```

## Key Components

### 1. LSP Server Extension

The LSP server provides:
- Real-time test discovery
- Test metadata extraction
- Requirement linkage detection
- Test quality analysis

### 2. Test Discovery Protocol

```typescript
interface TestInfo {
  id: string;              // Unique test identifier
  name: string;            // Test name
  filePath: string;        // Absolute file path
  range: Range;            // Location in file
  type: 'unit' | 'integration' | 'e2e';
  requirements: string[];  // Linked requirement IDs
  metadata: {
    description?: string;
    tags?: string[];
    complexity?: number;
  };
}

interface TestRegistrationRequest {
  method: 'metaTest/registerTests';
  params: {
    tests: TestInfo[];
    projectId: string;
  };
}
```

### 3. Integration Points

#### Editor Integration
- VS Code extension
- Neovim LSP client
- Other LSP-compatible editors

#### Meta-Test Integration
```python
class LSPTestRegistry:
    """Registry that receives test information from LSP."""
    
    async def handle_registration(self, request: TestRegistrationRequest):
        """Process test registration from LSP."""
        for test in request.tests:
            await self._store_test(test)
            await self._analyze_requirements(test)
            await self._calculate_initial_metrics(test)
```

## Benefits Over File Scanning

1. **Real-time Updates**: Tests are discovered as developers write them
2. **Accurate Parsing**: Uses proper language parsers, not regex
3. **Performance**: No repeated file system scanning
4. **IDE Integration**: Natural fit with development workflow
5. **Cross-language**: Works with any language that has LSP support

## Implementation Plan

### Phase 1: Protocol Definition
- Define LSP extensions for test discovery
- Create message schemas
- Document communication flow

### Phase 2: Server Implementation
- Extend existing LSP servers (pylsp, typescript-language-server)
- Add test discovery capabilities
- Implement meta-test specific analysis

### Phase 3: Client Integration
- Create editor plugins
- Implement registration endpoint
- Add UI for test quality feedback

### Phase 4: Meta-Test Integration
- Create LSP handler in meta-test
- Update graph schema for LSP metadata
- Implement real-time metric updates

## Example Usage

```python
# In your test file
def test_payment_processing():
    """Test payment processing.
    
    Requirements: req_payment_001, req_security_002
    """
    # Test implementation
    pass

# LSP automatically detects:
# - Test name: test_payment_processing
# - Requirements: ['req_payment_001', 'req_security_002']
# - Type: unit (inferred from location)
# - Description: "Test payment processing"
```

## Migration from File Scanning

1. Remove `auto_register_tests.py` ✓
2. Implement LSP test discovery
3. Create migration tool for existing test data
4. Update documentation
5. Provide editor setup guides

## Future Enhancements

- **Live Metrics**: Show test quality scores in editor
- **Requirement Completion**: Auto-complete requirement IDs
- **Test Generation**: Suggest tests for uncovered requirements
- **Refactoring Support**: Update test metadata during refactoring