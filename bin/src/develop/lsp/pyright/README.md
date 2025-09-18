# Minimal Pyright LSP Functionality

This directory provides a minimal implementation of Pyright functionality based on the POC results from `/home/nixos/bin/src/poc/develop/lsp/pyright/`.

## Purpose

The POC demonstrated that pyright-langserver can be used directly without LSMCP for full LSP capabilities. This implementation provides the essential Pyright features in a simplified flake structure with an LLM-first interface.

## Features

Based on the POC findings, this minimal implementation provides:

1. **Direct Pyright CLI** (`#check`) - Fast type checking using pyright directly
2. **LSP Protocol API** (`#lsp`) - Complete JSON-RPC interface for all LSP operations

## Usage

### Quick Start

```bash
# Show available commands
nix run /home/nixos/bin/src/develop/lsp/pyright

# Fast type checking with pyright CLI
nix run .#check -- example.py

# LSP protocol operations
echo '{"method": "textDocument/diagnostics", "params": {"file": "example.py"}}' | nix run .#lsp
echo '{"method": "textDocument/definition", "params": {"file": "example.py", "position": {"line": 10, "character": 5}}}' | nix run .#lsp
echo '{"method": "textDocument/references", "params": {"file": "example.py", "position": {"line": 10, "character": 5}}}' | nix run .#lsp
```

### Available Entry Points

| Command | Purpose | Input/Output |
|---------|---------|----------|
| `nix run .` | Show available commands | Text |
| `nix run .#check` | Direct pyright type checking | CLI args → Text |
| `nix run .#lsp` | LSP protocol access | JSON → JSON |
| `nix run .#test` | Run test suite | None → Test results |
| `nix run .#readme` | Show README | None → Markdown |

## LSP Protocol Examples

### Get Diagnostics
```bash
echo '{
  "method": "textDocument/diagnostics",
  "params": {"file": "app.py"}
}' | nix run .#lsp
```

### Find Definition
```bash
echo '{
  "method": "textDocument/definition",
  "params": {
    "file": "main.py",
    "position": {"line": 20, "character": 15}
  }
}' | nix run .#lsp
```

### Find References
```bash
echo '{
  "method": "textDocument/references",
  "params": {
    "file": "main.py",
    "position": {"line": 20, "character": 15}
  }
}' | nix run .#lsp
```

### Initialize LSP Server
```bash
echo '{
  "method": "initialize",
  "params": {"rootPath": "."}
}' | nix run .#lsp
```

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

## Practical Use Case: Safe Refactoring

When refactoring code, use the LSP API to ensure safety:

### 1. Find all references before changes
```bash
echo '{
  "method": "textDocument/references",
  "params": {
    "file": "example.py",
    "position": {"line": 10, "character": 15}
  }
}' | nix run .#lsp
```

### 2. Verify changes with type checking
```bash
nix run .#check -- example.py
```

### 3. Navigate to definitions as needed
```bash
echo '{
  "method": "textDocument/definition",
  "params": {
    "file": "example.py",
    "position": {"line": 20, "character": 10}
  }
}' | nix run .#lsp
```