#!/usr/bin/env -S nix shell nixpkgs#codex --command bash
# codex.sh - nixpkgs#codexを環境変数付きで起動するスクリプト

# OpenAI API Keyを設定（環境変数は親シェルを汚染しない）
export OPENAI_API_KEY="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"

# codexを実行
exec codex "$@"