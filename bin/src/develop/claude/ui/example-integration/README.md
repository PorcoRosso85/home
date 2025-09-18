# Example: Claude UI Flake Integration

This example demonstrates how to integrate Claude UI as a flake dependency in your own project.

## Two Integration Methods

### Method 1: Development Shell (devShell)
Add Claude UI to your development environment:

```bash
# Enter development shell
nix develop

# Now claude command is available
claude             # Launch in current directory
claude --flake     # Select project with fzf
claude /path/dir   # Launch in specific directory
```

### Method 2: Custom Wrappers (packages)
Create project-specific launchers:

```bash
# Custom wrapper with project configuration
nix run .#my-claude

# Specialized launcher using individual components
nix run .#project-launcher
```

## Key Benefits

- **No Path Dependencies**: Uses flake URL instead of file paths
- **System Independence**: Nix manages all dependencies
- **Clear Responsibility**: Uses only devShell and packages for integration
- **Flexible Integration**: Choose between development environment or custom wrappers
- **Backward Compatible**: Original `claude-shell.sh` continues to work

## Testing Note

For testing in this example directory, you may need to use `--impure` flag:
```bash
nix develop --impure
nix run --impure .#claude
```

In a real project with its own Git repository, this is not necessary.

## Adapting for Your Project

1. Copy the relevant parts from `flake.nix` to your project
2. Update the `claude-ui.url`:
   - For local testing: `"path:/home/nixos/bin/src/develop/claude/ui"`
   - For production: `"github:yourusername/claude-ui"`
3. Choose your preferred integration method (devShell or packages)
4. Customize as needed for your project requirements