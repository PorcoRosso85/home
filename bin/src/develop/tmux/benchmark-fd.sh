#!/usr/bin/env bash
# Benchmark fd search optimizations

echo "=== fd Search Benchmark ==="
echo "Searching for flake.nix files in $HOME"
echo

# 1. 基本的なfd検索
echo "1. Basic fd search:"
time fd -H -t f "flake.nix" "$HOME" 2>/dev/null | wc -l

echo -e "\n2. fd with -j 8 (8 threads):"
time fd -H -t f "flake.nix" "$HOME" -j 8 2>/dev/null | wc -l

echo -e "\n3. fd with exclusions:"
time fd -H -t f "flake.nix" "$HOME" \
  -E ".git" -E "node_modules" -E ".direnv" -E "result" -E ".cache" -E ".local" \
  2>/dev/null | wc -l

echo -e "\n4. fd with -j 8 and exclusions:"
time fd -H -t f "flake.nix" "$HOME" -j 8 \
  -E ".git" -E "node_modules" -E ".direnv" -E "result" -E ".cache" -E ".local" \
  2>/dev/null | wc -l

echo -e "\n5. fd with -j 16 and exclusions:"
time fd -H -t f "flake.nix" "$HOME" -j 16 \
  -E ".git" -E "node_modules" -E ".direnv" -E "result" -E ".cache" -E ".local" \
  2>/dev/null | wc -l