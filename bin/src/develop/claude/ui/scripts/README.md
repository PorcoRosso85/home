# Claude Launcher Scripts

Modular scripts for the Claude launcher system, packaged as independent Nix flakes.

## Available Scripts

### select-project
Interactive project selector using fzf. Allows selecting existing projects or creating new ones.

```bash
nix run .#select-project
```

### launch-claude
Launches Claude Code in a specified directory with optional conversation continuation.

```bash
nix run .#launch-claude -- /path/to/project [--continue]
```

## Building

```bash
# Build individual scripts
nix build .#select-project
nix build .#launch-claude

# Or build all
nix build
```

## Integration

These scripts are designed to be used as inputs in other flakes:

```nix
inputs.claude-scripts.url = "path:./scripts";
```