#!/usr/bin/env bash
# Run KuzuDB UDF test with required libraries

nix-shell -p stdenv.cc.cc.lib --run "LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/nix/store/*/lib uv run python test_minimal_udf.py"