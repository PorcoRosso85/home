#!/usr/bin/env bash
# firejail-claude.sh - Firejail wrapper for claude-shell.sh
# 起動ディレクトリのみ編集可能にするラッパー
#
# TODO: セキュリティ設定の選択肢
# 
# 1. オーバーレイファイルシステム（開発作業向け）
#    - ホーム全体の構造を維持（.gitconfig, .ssh等が使える）
#    - Claude Codeの設定・キャッシュが正常動作
#    - 書き込みはオーバーレイ層へ（元は変更されない）
#    使用例:
#    --overlay --overlay-named="claude_${PWD//\//_}" \
#    --bind="$WORK_DIR","$WORK_DIR"
#
# 2. プライベートホーム（POC・実験向け）
#    - 最もシンプルで安全
#    - 作業ディレクトリを仮想ホームとして使用
#    - 完全隔離だが設定ファイルが使えない
#    使用例:
#    --private="$WORK_DIR" --read-only="$HOME/.gitconfig:ro"
#
# 3. 現在の方式（ホワイトリスト）
#    - /home全体を読み取り専用
#    - 特定ディレクトリのみ書き込み許可
#    - Claude Codeのシステムファイル書き込み先を把握する必要あり

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

# execを使用してfirejailプロセスを置き換え、Claude終了時に自動的にfirejailも終了
exec firejail \
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