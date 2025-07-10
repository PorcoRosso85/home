# nix run コマンドUI設計

## 想定される使用パターン

### 1. 単一ファイル診断
```bash
# デフォルト（全ツール実行）
nix run .#python-diagnostics -- path/to/file.py

# 特定のチェックのみ
nix run .#python-diagnostics -- --check=type path/to/file.py
nix run .#python-diagnostics -- --check=lint path/to/file.py
nix run .#python-diagnostics -- --check=style path/to/file.py
```

### 2. パターンマッチング診断
```bash
# 基本パターン
nix run . -- -l python -p "*.py" diagnostics

# 再帰的パターン
nix run . -- -l python -p "src/**/*.py" diagnostics

# 複数パターン（カンマ区切り）
nix run . -- -l python -p "*.py,test_*.py" diagnostics
```

### 3. 出力フォーマット
```bash
# デフォルト（人間が読みやすい形式）
nix run . -- -l python -p "*.py" diagnostics

# JSON形式
nix run . -- -l python -p "*.py" diagnostics --format=json

# GitHub Actions形式
nix run . -- -l python -p "*.py" diagnostics --format=github

# 要約のみ
nix run . -- -l python -p "*.py" diagnostics --summary
```

## UI原則

1. **直感的**: 一般的なCLIツールの慣習に従う
2. **段階的詳細**: デフォルトは要約、詳細は要求時のみ
3. **カラー対応**: TTYの場合は色付き出力
4. **終了コード**: 
   - 0: エラーなし
   - 1: エラーあり
   - 2: 実行エラー

## 出力例

### デフォルト出力
```
Python Diagnostics Report
========================

Checking 3 files...

✗ src/main.py
  Line 10: [E] Undefined name 'undefined_var' (mypy)
  Line 15: [W] Line too long (85 > 79 characters) (flake8)
  
✓ src/utils.py
  No issues found

✗ tests/test_main.py
  Line 5: [E] Import error: No module named 'nonexistent' (mypy)

Summary: 2 errors, 1 warning in 2/3 files
```

### JSON出力
```json
{
  "summary": {
    "total_files": 3,
    "files_with_issues": 2,
    "total_errors": 2,
    "total_warnings": 1
  },
  "files": [
    {
      "path": "src/main.py",
      "issues": [
        {
          "line": 10,
          "column": 5,
          "severity": "error",
          "message": "Undefined name 'undefined_var'",
          "tool": "mypy"
        }
      ]
    }
  ]
}
```

## インタラクティブモード

```bash
# インタラクティブ選択
nix run . -- -l python --interactive

Select files to check:
[x] src/main.py
[ ] src/utils.py
[x] tests/test_main.py

Select tools to run:
[x] Syntax check
[x] Type checking (mypy)
[x] Linting (ruff)
[ ] Style (flake8)
[ ] Security (bandit)
```