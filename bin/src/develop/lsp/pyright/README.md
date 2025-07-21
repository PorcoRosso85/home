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

# Use LSP interface
nix run .#lsp -- check test_example.py
nix run .#lsp -- definition test_example.py 7 10
nix run .#lsp -- references test_example.py 7 10
```

### Available Commands

1. **Pyright Check** (Direct CLI)
   ```bash
   nix run .#check -- <file.py>
   ```
   Runs pyright's type checker directly on a Python file.

2. **LSP Interface**
   ```bash
   # Initialize LSP server (shows capabilities)
   nix run .#lsp -- init <workspace>
   
   # Get diagnostics via LSP
   nix run .#lsp -- check <file.py>
   
   # Go to definition
   nix run .#lsp -- definition <file> <line> <column>
   
   # Find all references
   nix run .#lsp -- references <file> <line> <column>
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