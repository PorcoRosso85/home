# Minimal Pyright LSP Functionality

This directory provides a minimal implementation of Pyright functionality based on the POC results from `/home/nixos/bin/src/poc/develop/lsp/pyright/`.

## Purpose

The POC demonstrated that pyright-langserver can be used directly without LSMCP for full LSP capabilities. This implementation provides the essential Pyright features in a simplified flake structure.

## Features

Based on the POC findings, this minimal implementation provides:

1. **Direct Pyright diagnostics** - Static type checking using pyright CLI
2. **LSP-based operations**:
   - Initialize LSP server
   - Get diagnostics via LSP protocol
   - Go to definition
   - Find references

## Usage

### Quick Start

```bash
# Check Python file for type errors
nix run .#check -- test_example.py

# Use LSP API (recommended)
echo '{"method": "textDocument/diagnostics", "params": {"file": "test_example.py"}}' | nix run .#lsp
echo '{"method": "textDocument/definition", "params": {"file": "test_example.py", "position": {"line": 7, "character": 10}}}' | nix run .#lsp
```

### Available Commands

1. **Pyright Check** (Direct CLI)
   ```bash
   nix run .#check -- <file.py>
   ```
   Runs pyright's type checker directly on a Python file.

2. **LSP API** (Recommended)
   ```bash
   # Show usage
   nix run .#lsp
   
   # Initialize LSP server (shows capabilities)
   echo '{"method": "initialize", "params": {"rootPath": "."}}' | nix run .#lsp
   
   # Get diagnostics
   echo '{"method": "textDocument/diagnostics", "params": {"file": "test.py"}}' | nix run .#lsp
   
   # Go to definition
   echo '{"method": "textDocument/definition", "params": {"file": "test.py", "position": {"line": 10, "character": 5}}}' | nix run .#lsp
   
   # Find all references
   echo '{"method": "textDocument/references", "params": {"file": "test.py", "position": {"line": 10, "character": 5}}}' | nix run .#lsp
   ```

## Test Example

The included `test_example.py` contains intentional type errors to demonstrate Pyright's capabilities:

```bash
# This will show type errors
nix run .#check -- test_example.py
```

Expected errors:
- Line 25: `calc.addd` - no attribute 'addd' (typo)
- Line 28: `calc.add("string", 10)` - type mismatch

## Development Shell

Enter the development environment:

```bash
nix develop
```

This provides:
- `pyright` - Direct access to pyright CLI
- `python3` - Python interpreter

## Architecture Notes

This implementation is intentionally minimal, providing only the essential Pyright functionality. For more advanced features like:
- Rename/refactoring
- Code actions
- Completions
- Hover information

Refer to the full POC implementation at `/home/nixos/bin/src/poc/develop/lsp/pyright/`.

## Key Differences from POC

1. **Simplified scope** - Only essential features
2. **No external dependencies** - No TypeScript, esbuild, or complex wrappers
3. **Pure Python LSP client** - Simple, readable implementation
4. **Focus on diagnostics** - Primary use case for type checking

## Practical Use Case: Function Renaming Workflow

When you need to rename a function (e.g., `calculate_average` → `compute_mean`):

### Step 1: Find all references before renaming
```bash
# Find all usages of calculate_average (at line 2, character 8)
echo '{"method": "textDocument/references", "params": {"file": "example_rename.py", "position": {"line": 2, "character": 8}}}' | nix run .#lsp
```

This will show:
- Line 2: Definition
- Line 10: Usage in process_data
- Line 20: Direct call
- Line 23: Another direct call

### Step 2: Verify definition location
```bash
# Confirm the definition location from a usage point
echo '{"method": "textDocument/definition", "params": {"file": "example_rename.py", "position": {"line": 20, "character": 25}}}' | nix run .#lsp
```

### Step 3: Make your changes
Manually edit the file to rename the function at all locations.

### Step 4: Verify no type errors after rename
```bash
# Quick check
nix run .#check -- example_rename.py

# Or detailed diagnostics
echo '{"method": "textDocument/diagnostics", "params": {"file": "example_rename.py"}}' | nix run .#lsp
```

If you missed any references, Pyright will report errors like:
- "No attribute 'calculate_average' on type 'DataProcessor'"

This workflow ensures safe refactoring by:
1. Identifying all usage locations before changes
2. Verifying changes don't introduce type errors
3. Providing clear error messages if references were missed