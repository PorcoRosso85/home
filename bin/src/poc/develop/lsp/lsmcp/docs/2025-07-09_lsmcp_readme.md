---
url: https://github.com/mizchi/lsmcp
saved_at: 2025-07-09T12:00:00Z
title: lsmcp - Language Service MCP
domain: github.com
---

# lsmcp - Language Service MCP

[](#lsmcp---language-service-mcp)

**LSP for headless AI Agents**

[CI - Unit Tests](https://github.com/mizchi/lsmcp/actions/workflows/ci-unit.yml) [CI - Integration Tests](https://github.com/mizchi/lsmcp/actions/workflows/ci-integration.yml) [CI - Language Adapters](https://github.com/mizchi/lsmcp/actions/workflows/ci-adapters.yml)

> ⚠️ **This project is under active development.** APIs and features may change without notice.

A unified MCP (Model Context Protocol) server that provides advanced code manipulation and analysis capabilities for multiple programming languages through Language Server Protocol integration.

## Features

[](#features)

- 🌍 **Multi-Language Support** - Built-in TypeScript/JavaScript, extensible to any language via LSP
- 🔍 **Semantic Code Analysis** - Go to definition, find references, type information
- 🤖 **AI-Optimized** - Designed for LLMs with line and symbol-based interfaces

### LSP Tools (Language Server Protocol)

[](#lsp-tools-language-server-protocol)

These tools work with any language that has an LSP server:

- **get\_hover** - Get hover information (type signature, documentation) using LSP
- **find\_references** - Find all references to symbol across the codebase using LSP
- **get\_definitions** - Get the definition(s) of a symbol using LSP
- **get\_diagnostics** - Get diagnostics (errors, warnings) for a file using LSP
- **get\_all\_diagnostics** - Get diagnostics (errors, warnings) for all files in the project
- **rename\_symbol** - Rename a symbol across the codebase using Language Server Protocol
- **delete\_symbol** - Delete a symbol and optionally all its references using LSP
- **get\_document\_symbols** - Get all symbols (functions, classes, variables, etc.) in a document using LSP
- **get\_workspace\_symbols** - Search for symbols across the entire workspace using LSP
- **get\_completion** - Get code completion suggestions at a specific position using LSP
- **get\_signature\_help** - Get signature help (parameter hints) for function calls using LSP
- **get\_code\_actions** - Get available code actions (quick fixes, refactorings, etc.) using LSP
- **format\_document** - Format an entire document using the language server's formatting provider

See [examples/](/mizchi/lsmcp/blob/main/examples) for working examples of each supported language configuration.

## Quick Start

[](#quick-start)

lsmcp provides multi-language support through Language Server Protocol (LSP) integration. The basic workflow is:

1. **Install Language Server** - Install the LSP server for your target language
1. **Add MCP Server** - Configure using `claude mcp add` command or `.mcp.json`

### Basic Usage

[](#basic-usage)

```
# Using presets for common languages
claude mcp add typescript npx -- -y @mizchi/lsmcp -p typescript

# Custom LSP server with --bin
claude mcp add <server-name> npx -- -y @mizchi/lsmcp --bin="<lsp-command>"
```

### Available Presets

[](#available-presets)

lsmcp includes built-in presets for popular language servers:

- **`typescript`** - TypeScript/JavaScript (typescript-language-server)
- **`tsgo`** - TypeScript/JavaScript (tsgo - faster alternative)
- **`deno`** - Deno TypeScript/JavaScript
- **`pyright`** - Python (Microsoft Pyright)
- **`ruff`** - Python (Ruff linter as LSP)
- **`rust-analyzer`** - Rust
- **`fsharp`** - F# (fsautocomplete)
- **`moonbit`** - MoonBit
- **`gopls`** - Go (Official Go language server)

For languages not in this list, or to customize LSP server settings, see [Manual Setup](#manual-setup).

### Language-Specific Setup

[](#language-specific-setup)

#### TypeScript

[](#typescript)

TypeScript Setup ```
# with typeScript-language-server (stable)
npm add -D typescript typescript-language-server
# Recommended: use tsgo for full functionality
claude mcp add typescript npx -- -y @mizchi/lsmcp -p typescript --bin="npx tsgo --lsp --stdio"

# with @typescript/native-preview (experimental, fast)
npm add -D @typescript/native-preview
claude mcp add typescript npx -- -y @mizchi/lsmcp -p typescript --bin="npx tsgo"
```

Manual Configuration (.mcp.json)

```
{
  "mcpServers": {
    "typescript": {
      "command": "npx",
      "args": [
        "-y",
        "@mizchi/lsmcp",
        "-p",
        "typescript",
        "--bin",
        "npx tsgo --lsp --stdio"
      ]
    }
  }
}
```

#### Rust

[](#rust)

Rust Setup ```
rustup component add rust-analyzer
claude mcp add rust npx -- -y @mizchi/lsmcp -p rust-analyzer
```

Manual Configuration (.mcp.json)

```
{
  "mcpServers": {
    "rust": {
      "command": "npx",
      "args": ["-y", "@mizchi/lsmcp", "-p", "rust-analyzer"]
    }
  }
}
```

See [examples/rust-project/](/mizchi/lsmcp/blob/main/examples/rust-project) for a complete example.

#### Go

[](#go)

Go Setup ```
# Install gopls (official Go language server)
go install golang.org/x/tools/gopls@latest
claude mcp add go npx -- -y @mizchi/lsmcp -p gopls
```

Manual Configuration (.mcp.json)

```
{
  "mcpServers": {
    "go": {
      "command": "npx",
      "args": ["-y", "@mizchi/lsmcp", "-p", "gopls"]
    }
  }
}
```

See [examples/go/](/mizchi/lsmcp/blob/main/examples/go) for a complete example.

#### F#

[](#f)

F# Setup ```
dotnet tool install -g fsautocomplete
claude mcp add fsharp npx -- -y @mizchi/lsmcp -p fsharp --bin="fsautocomplete --adaptive-lsp-server-enabled"
```

Manual Configuration (.mcp.json)

```
{
  "mcpServers": {
    "fsharp": {
      "command": "npx",
      "args": [
        "-y",
        "@mizchi/lsmcp",
        "-p",
        "fsharp",
        "--bin",
        "fsautocomplete"
      ]
    }
  }
}
```

See [examples/fsharp-project/](/mizchi/lsmcp/blob/main/examples/fsharp-project) for a complete example.

#### Python

[](#python)

Python Setup ```
# Option 1: Using Pyright (recommended)
npm install -g pyright
claude mcp add python npx -- -y @mizchi/lsmcp -p pyright

# Option 2: Using python-lsp-server
pip install python-lsp-server
claude mcp add python npx -- -y @mizchi/lsmcp --bin="pylsp"
```

Manual Configuration (.mcp.json)

```
{
  "mcpServers": {
    "python": {
      "command": "npx",
      "args": ["-y", "@mizchi/lsmcp", "-p", "pyright"]
    }
  }
}
```

See [examples/python-project/](/mizchi/lsmcp/blob/main/examples/python-project) for a complete example.

#### Other Languages

[](#other-languages)

Other Language Support lsmcp supports any language with an LSP server. Here are some common configurations:

```
# Go
go install golang.org/x/tools/gopls@latest
claude mcp add go npx -- -y @mizchi/lsmcp --bin="gopls"

# C/C++ 
# Install clangd from your package manager or LLVM releases
claude mcp add cpp npx -- -y @mizchi/lsmcp --bin="clangd"

# Java
# Install jdtls (Eclipse JDT Language Server)
claude mcp add java npx -- -y @mizchi/lsmcp --bin="jdtls"
```

For more customization options, see [Manual Setup](#manual-setup).

## Manual Setup

[](#manual-setup)

For advanced users who want more control over LSP server configuration, you can set up lsmcp manually with custom settings.

### Minimal rust-analyzer Example

[](#minimal-rust-analyzer-example)

```
{
  "mcpServers": {
    "rust-minimal": {
      "command": "npx",
      "args": [
        "-y",
        "@mizchi/lsmcp",
        "--bin",
        "rust-analyzer"
      ],
      "env": {
        "RUST_ANALYZER_CONFIG": "{\"assist\":{\"importGranularity\":\"module\"},\"cargo\":{\"allFeatures\":true}}"
      }
    }
  }
}
```

### Custom Language Server Setup

[](#custom-language-server-setup)

You can configure any LSP server by providing the binary path and optional initialization options:

```
{
  "mcpServers": {
    "custom-lsp": {
      "command": "npx",
      "args": [
        "-y",
        "@mizchi/lsmcp",
        "--bin",
        "/path/to/your/lsp-server",
        "--initializationOptions",
        "{\"customOption\":\"value\"}"
      ]
    }
  }
}
```

### Using Configuration Files

[](#using-configuration-files)

For complex LSP server configurations, you can use the `--config` option to load settings from a JSON file:

1. Create a configuration file (e.g., `my-language.json`):

```
{
  "id": "my-language",
  "name": "My Custom Language",
  "bin": "my-language-server",
  "args": ["--stdio"],
  "initializationOptions": {
    "formatOnSave": true,
    "lintingEnabled": true,
    "customFeatures": {
      "autoImport": true
    }
  }
}
```

1. Use it with lsmcp:

```
# Using Claude CLI
claude mcp add my-language npx -- -y @mizchi/lsmcp --config ./my-language.json

# Or in .mcp.json
{
  "mcpServers": {
    "my-language": {
      "command": "npx",
      "args": ["-y", "@mizchi/lsmcp", "--config", "./my-language.json"]
    }
  }
}
```

This approach is useful when:

- You have complex initialization options
- You want to share configurations across projects
- You need to version control your LSP settings

### Environment Variables

[](#environment-variables)

Some LSP servers can be configured via environment variables:

```
{
  "mcpServers": {
    "configured-lsp": {
      "command": "npx",
      "args": ["-y", "@mizchi/lsmcp", "--bin", "lsp-server"],
      "env": {
        "LSP_LOG_LEVEL": "debug",
        "LSP_WORKSPACE": "/path/to/workspace"
      }
    }
  }
}
```

## MCP Usage

[](#mcp-usage)

### Command Line Options

[](#command-line-options)

```
# Using language presets
npx @mizchi/lsmcp -p <preset> --bin '...'
npx @mizchi/lsmcp --preset <preset> --bin '...'

# Custom LSP server
npx @mizchi/lsmcp --bin '<lsp-command>'
```

## Development

[](#development)

```
# Install dependencies
pnpm install

# Build
pnpm build

# Run tests
pnpm test

# Type check
pnpm typecheck

# Lint
pnpm lint
```

See [CLAUDE.md](/mizchi/lsmcp/blob/main/CLAUDE.md) for development guidelines.

## Troubleshooting

[](#troubleshooting)

Common Issues ### LSP Server Not Found

[](#lsp-server-not-found)

```
Error: LSP server for typescript not found
```

**Solution**: Install the language server:

```
npm add typescript typescript-language-server
```

### Permission Denied

[](#permission-denied)

```
Error: Permission denied for tool 'rename_symbol'
```

**Solution**: Update `.claude/settings.json` to allow lsmcp tools.

### Empty Diagnostics

[](#empty-diagnostics)

If `get_diagnostics` returns empty results:

1. Ensure the language server is running: `ps aux | grep language-server`
1. Check for tsconfig.json or equivalent config file
1. Try opening the file first with `get_hover`

## License

[](#license)

MIT - See [LICENSE](/mizchi/lsmcp/blob/main/LICENSE) file for details.
warning: Git tree '/home/nixos' is dirty