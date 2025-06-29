#!/usr/bin/env bash
# 最小限のKuzuDB実行スクリプト

NIX_LD_LIBRARY_PATH=$(nix build nixpkgs#stdenv.cc.cc.lib --no-link --print-out-paths)/lib
LD_LIBRARY_PATH=$NIX_LD_LIBRARY_PATH:$LD_LIBRARY_PATH uv run "$@"