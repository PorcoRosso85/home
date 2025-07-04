#!/bin/bash
# POC 13.3 Integration Test Runner

echo "POC 13.3: Raft + Dynamic Service Orchestration Integration Tests"
echo "=============================================================="
echo ""

# Flake環境でテストを実行
cd "$(dirname "$0")"
nix develop --command deno test --allow-net integration.test.ts