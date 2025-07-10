# Python CLI診断問題の解決方法

## 問題の要約

LSMCPのPython診断機能には以下の問題があります：

1. **pylspの診断機能が不完全** - 実際のエラーを検出できない
2. **CLIバッチ処理未対応** - `--include`フラグはTypeScript/JavaScript専用
3. **MCPサーバーモード前提** - CLI単体使用は限定的

## 解決アプローチ

### 1. Nix Flakeによるラッパー実装

`flake.nix`で以下の機能を提供：

- **lsmcp-cli**: Python診断用の特別処理を含むラッパー
- **python-diagnostics**: 包括的なPython診断ツール

### 2. 複数のPythonツールを統合

pylsp単体では不十分なため、以下のツールを組み合わせます：

```bash
# 型チェック
mypy main.py

# Linting（高速・包括的）
ruff check main.py

# コードスタイル
flake8 main.py

# セキュリティチェック
bandit -r main.py
```

## 使用方法

### セットアップ

```bash
cd /home/nixos/bin/src/poc/develop/lsp
nix develop
```

### Python診断の実行

#### 方法1: ラッパー経由

```bash
# 特定パターンのファイルを診断
lsmcp-cli -l python -c diagnostics -p '*.py'

# 特定ディレクトリ配下を診断
lsmcp-cli -l python -c diagnostics -p 'src/**/*.py'
```

#### 方法2: 直接診断ツール

```bash
# 単一ファイルの包括的診断
python-diagnostics main.py
```

#### 方法3: 個別ツール

```bash
# 型チェックのみ
mypy main.py

# Lintingのみ
ruff check main.py

# すべてのPythonファイルをチェック
find . -name "*.py" -exec python-diagnostics {} \;
```

## 実装の詳細

### lsmcp-cliラッパー

1. 言語とコマンドを判定
2. Python診断の場合は専用処理にフォールバック
3. その他は通常のlsmcpを実行

### python-diagnostics

1. **構文チェック**: `python -m py_compile`
2. **型チェック**: mypy
3. **Linting**: ruff
4. **コードスタイル**: flake8
5. **セキュリティ**: bandit

## 既知の制限事項と回避策

### 1. プロジェクト全体の解析

LSMCPはプロジェクト全体の依存関係を理解できません。

**回避策**: プロジェクトルートで実行し、設定ファイルを使用

```bash
# pyproject.tomlやsetup.cfgがあるディレクトリで実行
cd /path/to/project
python-diagnostics src/main.py
```

### 2. インポートエラーの検出

pylspはインポートエラーを見逃すことがあります。

**回避策**: mypyを使用

```bash
mypy --strict main.py
```

### 3. リアルタイム診断

CLIでは編集中のリアルタイム診断はできません。

**回避策**: ファイル保存時にフックで実行

```bash
# Git pre-commitフック例
#!/bin/bash
for file in $(git diff --cached --name-only | grep '\.py$'); do
    python-diagnostics "$file" || exit 1
done
```

## 他言語への応用

同様のアプローチで他言語のCLI診断も改善可能：

```nix
# Rust用
rustDiagnostics = pkgs.writeShellScriptBin "rust-diagnostics" ''
  cargo check
  cargo clippy
  cargo fmt --check
'';

# Go用
goDiagnostics = pkgs.writeShellScriptBin "go-diagnostics" ''
  go vet ./...
  golangci-lint run
  go fmt ./...
'';
```

## まとめ

LSMCPのPython CLI問題は、Nix Flakeでラッパーを作成し、複数の専用ツールを組み合わせることで解決できます。この方法により、より正確で包括的な診断が可能になります。