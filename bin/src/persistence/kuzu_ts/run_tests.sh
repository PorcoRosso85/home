#!/usr/bin/env bash
# Simple test runner without temp directory copying

# Set up environment
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}/nix/store/*/lib"

# Run tests directly from current directory
echo "Running tests..."
deno test tests/*.test.ts \
  --allow-read \
  --allow-write \
  --allow-net \
  --allow-env \
  --allow-ffi \
  --unstable-ffi \
  --no-check