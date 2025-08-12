#!/usr/bin/env bash
# lsmcp - Language Service MCP server
# Uses nix shell for dependency management (following conventions/nix_flake.md)

# Note: rust-analyzer requires system installation or rustup
# pyright is included but may have timeout issues with lsmcp

exec nix shell \
  nixpkgs#nodejs_22 \
  nixpkgs#nodePackages.typescript-language-server \
  nixpkgs#nodePackages.typescript \
  nixpkgs#gopls \
  nixpkgs#pyright \
  nixpkgs#nodePackages.vscode-langservers-extracted \
  --command npx -y @mizchi/lsmcp "$@"