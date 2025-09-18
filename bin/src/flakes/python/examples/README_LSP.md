# Python LSP Examples

このディレクトリには、pyrightとruffのLSP機能を活用した実践例が含まれています。

## 構造

```
examples/
├── absolute_imports/     # 絶対インポートのサンプルプロジェクト
├── relative_imports/     # 相対インポートのサンプルプロジェクト
├── lsp_knowledge.md      # LSP知見のドキュメント
├── lsp_refactoring_demo.py  # リファクタリングデモ
├── refactor_with_lsp.py  # LSPを使ったリファクタリングツール
└── pyproject.toml        # pyright/ruff設定例
```

## クイックスタート

### 1. 型チェックの実行

```bash
# 絶対インポートプロジェクトをチェック
nix develop -c pyright examples/absolute_imports/

# 相対インポートプロジェクトをチェック
nix develop -c pyright examples/relative_imports/
```

### 2. リンターの実行

```bash
# Ruffでスタイルチェック
nix develop -c ruff check examples/

# 自動修正付き
nix develop -c ruff check --fix examples/
```

### 3. LSPサーバーの起動

```bash
# Pyright LSP
nix develop -c pyright --langserver --stdio

# Ruff LSP
nix develop -c ruff serve
```

## 学習ポイント

1. **インポートスタイルの違い**
   - `absolute_imports/`: プロジェクトルートからの絶対パス
   - `relative_imports/`: 現在位置からの相対パス

2. **LSPの利点**
   - リアルタイムエラー検出
   - インポートパスの検証
   - 型情報の提供
   - リファクタリング支援

3. **設定ファイル**
   - `pyproject.toml`: pyright/ruffの設定例
   - 厳密度の段階的適用が可能

## 次のステップ

詳細な知見については `lsp_knowledge.md` を参照してください。