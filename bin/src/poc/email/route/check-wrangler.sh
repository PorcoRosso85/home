#!/usr/bin/env nix-shell
#!nix-shell -i bash -p wrangler

echo "Checking wrangler availability..."
which wrangler
echo ""
echo "Wrangler version:"
wrangler --version