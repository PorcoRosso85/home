#!/usr/bin/env bash
# Flakeテスト実行スクリプト

cd "$(dirname "$0")"

echo "R2 SDK Flakeのテストを実行します..."
echo ""

# pytestがインストールされた環境でテストを実行
nix-shell -p python3 python3Packages.pytest --run "pytest test_flake.py -v $@"