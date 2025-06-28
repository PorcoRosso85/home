#!/usr/bin/env bash
# Test runner script with required environment variables

export LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/
export RGL_DB_PATH=/tmp/test_rgl_db
export RGL_SKIP_SCHEMA_CHECK=true

uv run pytest "$@"