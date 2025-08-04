#!/usr/bin/env bash
# claude-launcher.sh - Simple wrapper for nix run

exec nix run .#core "$@"