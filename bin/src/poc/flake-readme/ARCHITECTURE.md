# flake-readme Architecture

## Design Principles

### ignore-only Policy (Current Implementation)
- **Rule**: All directories require `readme.nix` unless explicitly ignored
- **Implementation**: `listMissingReadmes` function in `lib/core-docs.nix`
- **Separation**: Fact collection (`isDocumentable`) separate from policy enforcement

### Single Responsibility Principle
- **Fact Collection**: `isDocumentable` tracks which directories contain .nix files
- **Policy Enforcement**: `listMissingReadmes` determines what requires documentation
- **Validation**: `validateDoc` ensures documentation quality

## Key Functions
- `collect()`: Gather readme.nix files from filesystem
- `normalizeDoc()`: Convert to v1 schema
- `validateDoc()`: Quality and structure validation
- `index()`: Complete workflow with missing detection

## Extension Points
- `ignoreExtra`: Additional ignore patterns beyond default
- `missingIgnoreExtra`: Separate ignore for missing detection (if needed)

## Policy Implementation Details

### Current ignore-only Policy
```nix
# All directories require readme.nix unless in defaultIgnore list
defaultIgnore = name: type:
  builtins.elem name [
    ".git" ".direnv" "node_modules" "result" "dist" "target" ".cache"
  ] || (name == "examples" && type == "directory");
```

### Architectural Separation
1. **Fact Collection (`isDocumentable`)**:
   - Tracks directories containing .nix files
   - Pure fact, no policy decisions
   - Available for future policy extensions

2. **Policy Enforcement (`listMissingReadmes`)**:
   - Implements ignore-only rule
   - Uses only ignore patterns, not `isDocumentable`
   - Achieves Single Responsibility Principle separation

### Future Extension Design
The architecture supports policy evolution:
- `isDocumentable` facts remain available for smarter policies
- Current ignore-only approach provides predictable baseline
- Extension points allow customization without architectural changes