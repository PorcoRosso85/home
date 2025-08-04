#!/usr/bin/env bash
# tmux-shell.sh - Fast tmux launcher using nix shell
# Avoids nix run overhead by using nix shell directly

set -euo pipefail

# Show help if requested
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [options]"
    echo ""
    echo "Fast tmux session launcher using nix shell"
    echo "Creates a tmux session with 2-pane layout and development tools"
    echo ""
    echo "This script uses 'nix shell' for fast startup (0.1s vs 20s with nix run)"
    exit 0
fi

# Launch tmux with required dependencies
exec nix shell \
    nixpkgs#tmux \
    nixpkgs#lazygit \
    nixpkgs#yazi \
    nixpkgs#git \
    nixpkgs#coreutils \
    nixpkgs#bash \
    nixpkgs#fzf \
    nixpkgs#fd \
    nixpkgs#jq \
    --command bash "$(dirname "$0")/main.sh" "$@"