# pyright/ruff ネイティブ機能ガイド

このディレクトリには、pyrightとruffの素の機能をそのまま使用する例が含まれています。

## 概要

pyrightとruffは、それぞれ独立したコマンドラインツールとして動作します。このガイドでは、これらのツールの素の機能を直接使用する方法を示します。

## ファイル一覧

### 1. `import_converter_with_lsp.py`
pyrightとruffのコマンドを直接呼び出すPythonスクリプト。

```python
# pyrightの素の機能を使用
subprocess.run(["pyright", "--outputjson", "main.py"])

# ruffの素の機能を使用
subprocess.run(["ruff", "check", "--output-format", "json", "main.py"])
```

### 2. `native_lsp_usage.py`
各ツールのネイティブコマンドの使い方を説明するドキュメント型スクリプト。

### 3. `ruff_import_sorter.sh`
ruffの素の機能だけを使用したシェルスクリプト。

## pyright の素の機能

### 基本的な使い方

```bash
# 型チェック
pyright main.py

# JSON形式で詳細情報を取得
pyright --outputjson main.py

# 統計情報付き
pyright --stats

# ファイル監視モード
pyright --watch

# 設定ファイルを指定
pyright --project pyrightconfig.json
```

### pyrightconfig.json の例

```json
{
  "include": ["src"],
  "exclude": ["**/__pycache__"],
  "reportMissingImports": true,
  "pythonVersion": "3.12"
}
```

## ruff の素の機能

### 基本的な使い方

```bash
# リンティング
ruff check .

# インポート関連のみチェック
ruff check --select I .

# 自動修正
ruff check --fix .

# 修正内容をプレビュー
ruff check --fix --diff .

# フォーマット
ruff format .

# JSON出力
ruff check --output-format json .
```

### インポート整理の例

```bash
# インポート順序をチェック
ruff check --select I001 main.py

# インポートを自動整理
ruff check --select I --fix main.py

# 変更内容を確認
ruff check --select I --fix --diff main.py
```

## 実践例

### 1. インポートエラーの検出と修正

```bash
# pyrightでインポートエラーを検出
pyright --outputjson main.py | jq '.generalDiagnostics[] | select(.message | contains("import"))'

# ruffでインポート順序を修正
ruff check --select I --fix main.py
```

### 2. シェルスクリプトでの組み合わせ

```bash
#!/bin/bash
# 両方のツールを実行
echo "=== Pyright ==="
pyright "$1"

echo -e "\n=== Ruff ==="
ruff check "$1"
```

### 3. エディタ統合

#### VSCode
```json
{
  "python.linting.enabled": false,
  "python.analysis.typeCheckingMode": "strict",
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

#### Neovim (LSP設定)
```lua
-- pyrightの設定
require'lspconfig'.pyright.setup{}

-- ruff-lspの設定
require'lspconfig'.ruff_lsp.setup{
  init_options = {
    settings = {
      args = {"--select", "I"},
    }
  }
}
```

## 使用例

### ruff_import_sorter.sh の使用

```bash
# インポートをチェック
./ruff_import_sorter.sh main.py

# 修正案を表示
./ruff_import_sorter.sh --diff main.py

# 実際に修正
./ruff_import_sorter.sh --fix main.py

# ディレクトリ全体を処理
./ruff_import_sorter.sh --fix src/
```

### import_converter_with_lsp.py の使用

```bash
# デモを実行
python import_converter_with_lsp.py --demo

# インタラクティブモード
python import_converter_with_lsp.py --interactive

# 単一ファイルを分析
python import_converter_with_lsp.py main.py

# LSP機能の説明を表示
python import_converter_with_lsp.py --capabilities
```

## まとめ

- pyrightとruffは独立したツールとして素の機能を提供
- コマンドラインから直接使用可能
- JSON出力により他のツールと連携が容易
- シェルスクリプトやPythonから呼び出して自動化可能
- エディタのLSP機能と統合して使用可能

これらの素の機能を理解することで、必要に応じて柔軟にツールを組み合わせることができます。