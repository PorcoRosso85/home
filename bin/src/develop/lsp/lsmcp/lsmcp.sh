#!/usr/bin/env bash
# lsmcp - Language Service MCP server
# Uses nix shell for dependency management (following conventions/nix_flake.md)

exec nix shell \
  nixpkgs#nodejs_22 \
  nixpkgs#nodePackages.typescript-language-server \
  nixpkgs#nodePackages.typescript \
  nixpkgs#gopls \
  nixpkgs#pyright \
  nixpkgs#nodePackages.vscode-langservers-extracted \
  nixpkgs#cargo \
  nixpkgs#rustc \
  --command npx -y @mizchi/lsmcp "$@"