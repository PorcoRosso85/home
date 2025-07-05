# Flake Usage Guide

## 開発環境

```bash
# 開発シェルに入る
nix develop

# コマンドを実行
nix develop --command python search_standalone.py ./test_data
```

## コマンド実行

```bash
# シンボル検索
nix run . -- ./path/to/search

# ファイルURLも対応
nix run . -- file:///absolute/path/to/file.py

# JSON出力をjqで処理
nix run . -- ./src | jq '.symbols[] | select(.type == "class")'
```

## テスト

```bash
# テスト実行
nix run .#test

# フォーマット
nix run .#format

# リント
nix run .#lint

# 型チェック
nix run .#typecheck
```

## 特徴

- 最小限のflake設定
- スタンドアロン実装（依存関係の問題を回避）
- convention準拠のテスト
- 標準的なPython開発ツール（pytest, black, ruff, mypy）