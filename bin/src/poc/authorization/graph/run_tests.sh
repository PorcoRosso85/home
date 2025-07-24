#!/usr/bin/env bash
set -e

# Python環境をセットアップ
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# nixpkgsのpythonを使用
nix-shell -p python311 python311Packages.pytest python311Packages.kuzu --run "python -m pytest tests/ -v --tb=short"