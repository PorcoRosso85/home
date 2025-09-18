#!/usr/bin/env -S nix shell nixpkgs#bash nixpkgs#coreutils --command bash

# テスト: nix shell shebangが機能するか確認
echo "✅ Shebang with nix shell is working!"
echo "Current shell: $SHELL"
echo "Bash version: $BASH_VERSION"
echo "Date command from coreutils: $(date)"