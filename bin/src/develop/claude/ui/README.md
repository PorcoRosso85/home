# Claude Launcher - Modular Architecture

A modular, composable system for launching Claude Code with automatic project selection via fzf.

## Overview

This project provides a flexible way to launch Claude Code in different project contexts. It's built with a modular architecture that allows each component to be used independently or integrated into other workflows.

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

## Installation & Usage

### Quick Start

```bash
# Clone the repository
git clone <repository-url> claude-launcher
cd claude-launcher

# One-time setup: Configure MCP servers at user scope
./setup-mcp-user.sh

# Launch Claude in current directory (0.1s startup)
./claude-shell.sh

# Launch Claude in specific directory
./claude-shell.sh ~/projects/myproject

# Launch Claude with fzf project selector (for flake.nix projects)
./claude-shell.sh --flake
```

That's it! The launcher uses `nix shell` to provide dependencies on-demand without requiring a complex flake setup.

### Using Components Separately

Each component can be built and used independently:

```bash
# Build individual components
nix build .#select-project
nix build .#launch-claude

# Use them separately
PROJECT=$(nix run .#select-project)
nix run .#launch-claude -- "$PROJECT" --continue
```

## Integration Examples

### Custom Shell Script Integration

```bash
#!/usr/bin/env bash
# my-claude-workflow.sh

# Use select-project with custom root
PROJECT=$(nix run github:your-repo/claude-launcher#select-project -- -r ~/work)

# Add custom logic
if [[ "$PROJECT" == *"sensitive"* ]]; then
  echo "Warning: Sensitive project selected"
  read -p "Continue? (y/n) " -n 1 -r
  echo
  [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# Launch with custom behavior
nix run github:your-repo/claude-launcher#launch-claude -- "$PROJECT"
```

### Nix Flake Integration

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    claude-launcher.url = "github:your-repo/claude-launcher";
  };

  outputs = { self, nixpkgs, claude-launcher }: {
    # Use individual components in your own packages
    packages.x86_64-linux.my-tool = pkgs.writeShellApplication {
      name = "my-tool";
      runtimeInputs = [
        claude-launcher.packages.x86_64-linux.select-project
        claude-launcher.packages.x86_64-linux.launch-claude
      ];
      text = ''
        # Your custom workflow using the modular components
        project=$(select-project -r ~/special-projects)
        # ... custom logic ...
        launch-claude "$project"
      '';
    };
  };
}
```

### Direct Component Usage

```bash
# Just project selection
nix run .#select-project -- --debug --root ~/projects

# Just launching (when you already know the directory)
nix run .#launch-claude -- ~/my-project --continue

# In scripts
alias select-claude-project='nix run github:your-repo/claude-launcher#select-project'
alias launch-claude='nix run github:your-repo/claude-launcher#launch-claude'
```

## Testing

The project includes comprehensive tests:

```bash
# Run all tests
nix flake check

# Run tests with output
nix run .#test

# Run individual test files
bats test_select_project.bats
bats test_launch_claude.bats
bats test_e2e_integrated.bats
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

## MCP Server Configuration

### User Scope Setup (Recommended)

MCP servers are configured at user scope, making them available across all projects:

```bash
# One-time setup
./setup-mcp-user.sh

# This configures:
# - lsmcp: Language Server MCP at /home/nixos/bin/src/develop/lsp/lsmcp
# - Add more servers by modifying setup-mcp-user.sh
```

### Why User Scope?

- **Global availability**: Configured once, available everywhere
- **No project pollution**: No `.mcp.json` files in your projects
- **Centralized management**: Update servers in one place
- **Dynamic configuration**: No static files to maintain

## Common Use Cases

### CI/CD Integration
Use `launch-claude` directly when the project directory is known:
```yaml
- run: nix run .#launch-claude -- ${{ github.workspace }}
```

### Interactive Development
Use the full launcher for interactive project selection:
```bash
./claude-shell.sh
```

### Custom Project Organization
Create wrappers that use `select-project` with different roots:
```bash
# Work projects
alias claude-work='./scripts/select-project -r ~/work | xargs ./scripts/launch-claude'

# Personal projects  
alias claude-personal='./scripts/select-project -r ~/personal | xargs ./scripts/launch-claude'
```

## License

See LICENSE file in the repository root.