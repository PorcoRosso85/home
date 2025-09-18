# Tmux Development Environment

A fast, Nix-based tmux configuration optimized for development workflows. This project provides an instant-launch tmux environment with pre-configured layouts and development tools.

## Key Features

- **2-pane/4-pane layouts**: Window 0 has 2 panes (lazygit/yazi), subsequent windows auto-create with 4 panes
- **Flake directory search**: Quick navigation to any flake.nix project with `Ctrl-b c`
- **Smart pane management**: Auto-recreation of panes on exit, consistent layouts
- **FZF integration**: Jump between panes with `Ctrl-b b`

## Usage

```bash
./tmux-shell.sh  # Recommended: Fast startup using nix shell
```

## Key Bindings

- `Ctrl-b 0/1`: Switch windows
- `Ctrl-b h/j/k/l`: Navigate panes (vim-style)
- `Ctrl-b c`: Search and open flake directories
- `Ctrl-b b`: FZF pane jump
- `Ctrl-b v`: Copy mode

## Why nix shell?

Switched from `nix run` to `nix shell` for 200x faster startup (0.1s vs 20s). The launcher script (`tmux-shell.sh`) pulls required dependencies (tmux, lazygit, yazi, fzf) and executes main.sh directly, avoiding Nix evaluation overhead.