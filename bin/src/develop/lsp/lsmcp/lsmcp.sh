#!/usr/bin/env nix-shell
#!nix-shell -i bash
#!nix-shell -p nodejs_20
#!nix-shell -p nodePackages.typescript-language-server
#!nix-shell -p nodePackages.typescript  
#!nix-shell -p rust-analyzer
#!nix-shell -p gopls
#!nix-shell -p pyright
#!nix-shell -p nodePackages.vscode-langservers-extracted

# lsmcp - Language Service MCP server
# Direct execution without flake.nix

exec npx -y @mizchi/lsmcp "$@"