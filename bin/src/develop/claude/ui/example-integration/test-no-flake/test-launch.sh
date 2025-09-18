#!/usr/bin/env bash
# Debug version of launch-claude to show errors

set -euo pipefail

TARGET_DIR="$(pwd)"
echo "Testing in: $TARGET_DIR"
echo "flake.nix exists: $([ -f flake.nix ] && echo 'yes' || echo 'no')"

# Test with --continue and show errors
echo ""
echo "Testing --continue (with error output):"
if env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --continue --dangerously-skip-permissions 2>&1; then
  echo "Continue succeeded"
else
  echo "Continue failed with exit code: $?"
fi