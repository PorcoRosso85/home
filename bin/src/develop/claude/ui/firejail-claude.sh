#!/usr/bin/env bash
# firejail-claude.sh - Firejail wrapper for claude-shell.sh
# 起動ディレクトリのみ編集可能にするラッパー

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(pwd)"

# MCP設定済みチェック（Firejail外で実行）
if [[ ! -f "$HOME/.claude.json" ]]; then
    echo "Error: MCP not configured. Run setup-mcp-user.sh first."
    exit 1
fi

# MCPディレクトリも読み書き可能にする
MCP_DIR="$HOME/.claude"

# Firejailで制限付きClaude起動
# - 起動ディレクトリ: 読み書き可能
# - claude/ui以下のスクリプト: 読み取り可能
# - ~/.claude.json, ~/.claude/: 読み書き可能（MCP設定のため）
# - /nix: 読み取り可能（Nixパッケージ）
# - /tmp: 読み書き可能（一時ファイル）

firejail \
  --noprofile \
  --read-only=/home \
  --read-write="$WORK_DIR" \
  --read-write="$HOME/.claude.json" \
  --read-write="$MCP_DIR" \
  --read-only="$SCRIPT_DIR" \
  --read-only=/nix \
  --read-write=/tmp \
  --quiet \
  -- "$SCRIPT_DIR/claude-shell.sh" "$@"