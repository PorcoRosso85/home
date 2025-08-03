# Strict Python Type Checking Configuration

This directory contains strict configuration for Python type checking that enforces maximum type safety, similar to TypeScript's strict mode.

## Configuration Files

### pyrightconfig.json
A strict Pyright/Pylance configuration with maximum type safety:
- `typeCheckingMode: "strict"` - Enables strict type checking mode
- All diagnostic rules set to "error" level
- Strict inference for collections (lists, dicts, sets)
- No type ignore comments allowed
- Verbose output for detailed diagnostics

## Usage

### With Pyright/Pylance
```bash
# Run pyright (it automatically detects pyrightconfig.json)
pyright your_file.py

# Or use with VS Code Pylance extension (automatic)
```

## Comparison with TypeScript

This configuration enforces type safety similar to TypeScript's `"strict": true`:

| TypeScript strict flag | Pyright equivalent |
|------------------------|-------------------|
| `noImplicitAny` | `reportUnknownParameterType`, `reportUnknownArgumentType` |
| `strictNullChecks` | `reportOptionalMemberAccess`, `reportOptionalCall` |
| `strictFunctionTypes` | `reportGeneralTypeIssues` |
| `strictBindCallApply` | N/A (Python doesn't have these methods) |
| `strictPropertyInitialization` | `reportUninitializedInstanceVariable` |
| `noImplicitThis` | N/A (Python has explicit `self`) |
| `alwaysStrict` | Default in Python 3 |
| `useUnknownInCatchVariables` | `reportUnknownVariableType` |

## Key Benefits

1. **Early Error Detection**: Catches type errors before runtime
2. **Better IDE Support**: Enhanced autocomplete and refactoring
3. **Self-Documenting Code**: Types serve as inline documentation
4. **Safer Refactoring**: Type checker validates changes
5. **Gradual Adoption**: Can be enabled per-file or per-module

## Example Type Errors Caught

These configurations will catch common errors like:
- Type mismatches in assignments
- Accessing properties on `None` values
- Missing function arguments
- Accessing non-existent attributes
- Modifying immutable data structures

See `error_patterns.py` for examples of errors these configurations catch.