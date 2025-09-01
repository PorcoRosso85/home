#!/usr/bin/env bash
set -euo pipefail

# Python wrapper script for nix-shell
exec nix-shell -p python312Packages.kuzu --run "python readme_graph.py $*"