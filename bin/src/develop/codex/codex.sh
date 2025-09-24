#!/usr/bin/env bash
# codex.sh - Nix-packaged Codex CLI を呼び出す薄いラッパ
set -euo pipefail

# ローカル環境変数を読み込み（存在する場合のみ）
if [ -f "./env.sh" ]; then
  # shellcheck disable=SC1091
  . "./env.sh"
fi

# 必須環境変数の確認
if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "ERROR: OPENAI_API_KEY is not set. Export it or create env.sh." >&2
  exit 1
fi

# 実行例 (flake パッケージ経由):
#   nix shell .#codex -c ./codex.sh --continue

exec codex "$@"
