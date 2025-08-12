#!/usr/bin/env bash
# lsmcp - Language Service MCP server
# Uses nix shell for dependency management (following conventions/nix_flake.md)

exec nix shell \
  nixpkgs#nodejs_20 \
  nixpkgs#nodePackages.typescript-language-server \
  nixpkgs#nodePackages.typescript \
  nixpkgs#rust-analyzer \
  nixpkgs#gopls \
  nixpkgs#pyright \
  nixpkgs#nodePackages.vscode-langservers-extracted \
  --command npx -y @mizchi/lsmcp "$@"