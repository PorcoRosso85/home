# Claude Launcher

A simple launcher for Claude Code with automatic project selection via fzf, designed for development environments.

## Overview

This project provides a simple way to launch Claude Code in different project contexts using fzf for interactive selection. It's designed to work with `nix develop` for dependency management.

## Architecture

The system consists of three main components:

### 1. `select-project` - Project Selection Module
- **Purpose**: Interactive project selector using fzf
- **Features**:
  - Finds all projects with `flake.nix` files
  - Allows selecting existing projects or creating new ones
  - Configurable search root directory
  - Debug logging support
- **Exit codes**: 0 (success), 1 (cancelled/error)
- **Output**: Selected project directory path to stdout

### 2. `launch-claude` - Claude Launcher Module
- **Purpose**: Launches Claude Code in a specified directory
- **Features**:
  - Simple directory-based launching
  - Support for `--continue` flag to resume conversations
  - Automatic `NIXPKGS_ALLOW_UNFREE=1` setting
  - Clear error messages and help text
- **Usage**: `launch-claude <directory> [--continue]`

### 3. `claude-launcher` - Integrated Launcher
- **Purpose**: Combines both modules for a complete workflow
- **Features**:
  - Uses `select-project` to choose a project
  - Automatically detects if `--continue` mode should be used
  - Seamless integration of both components

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd claude-launcher

# Enter development environment
nix develop

# Or run directly without entering the shell
nix develop -c ./claude-launcher
```

## Usage Examples

### Basic Usage

```bash
# Run the main launcher
nix develop -c ./claude-launcher

# Use individual scripts
nix develop -c ./scripts/select-project
nix develop -c ./scripts/launch-claude ~/my-project --continue
```

### Shell Aliases

```bash
# Add to your ~/.bashrc or ~/.zshrc
alias claude='cd /path/to/claude-launcher && nix develop -c ./claude-launcher'
alias claude-select='cd /path/to/claude-launcher && nix develop -c ./scripts/select-project'
```

### Custom Integration

```bash
#!/usr/bin/env bash
# my-workflow.sh
cd /path/to/claude-launcher
project=$(nix develop -c ./scripts/select-project -r ~/work)
nix develop -c ./scripts/launch-claude "$project"
```

## Testing

```bash
# Run all tests
nix develop -c bats test_*.bats

# Run specific test file
nix develop -c bats test_e2e_integrated.bats

# Lint scripts
nix develop -c shellcheck scripts/*
```

## Development

```bash
# Enter development shell
nix develop

# Available tools:
# - bash-language-server
# - shellcheck
# - shfmt
# - bats (for testing)
```

## Component Documentation

### select-project

```
Usage: select-project [OPTIONS]

Options:
  -h, --help     Show help message
  -d, --debug    Enable debug logging
  -r, --root DIR Start search from DIR (default: current directory)

Exit codes:
  0  Success - project directory selected/created
  1  Cancelled or error occurred
```

### launch-claude

```
Usage: launch-claude <directory> [--continue]

Arguments:
  <directory>     The directory to launch Claude in (required)
  --continue      Resume previous conversation if available
  --help          Show help message

Environment:
  Sets NIXPKGS_ALLOW_UNFREE=1 automatically
```

## Benefits of Modular Architecture

1. **Flexibility**: Use only the components you need
2. **Composability**: Integrate with existing workflows
3. **Testability**: Each component can be tested independently
4. **Maintainability**: Clear separation of concerns
5. **Reusability**: Components can be used in other projects

## Common Use Cases

### CI/CD Integration
Use `launch-claude` directly when the project directory is known:
```yaml
- run: nix run .#launch-claude -- ${{ github.workspace }}
```

### Interactive Development
Use the full launcher for interactive project selection:
```bash
nix run .#claude-launcher
```

### Custom Project Organization
Create wrappers that use `select-project` with different roots:
```bash
# Work projects
alias claude-work='nix run .#select-project -- -r ~/work | xargs nix run .#launch-claude --'

# Personal projects  
alias claude-personal='nix run .#select-project -- -r ~/personal | xargs nix run .#launch-claude --'
```

## License

See LICENSE file in the repository root.