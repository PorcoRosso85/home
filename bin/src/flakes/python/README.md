# Python共通環境

bin/src配下のPythonプロジェクトで使用する共通環境を提供します。

## ディレクトリ構造

```
python/
├── mod.py                      # 公開API
├── variables.py                # 環境変数管理
├── infrastructure/             # 実行器層
│   ├── vessel_pyright.py       # Pyright実行環境
│   └── vessel_python.py        # Python/pytest/ruff実行環境
├── domain/                     # ビジネスロジック層
│   └── validation.py           # 出力検証ロジック
├── examples/                   # 使用例
│   ├── check_types.py          # 型チェック例
│   ├── combined_analysis.py    # 統合分析例
│   ├── lint_and_fix.py         # リンティング例
│   └── test_and_report.py      # テスト実行例
├── tests/                      # テスト
│   ├── test_validation.py      # 検証ロジックのテスト
│   ├── test_variables.py       # 環境変数管理のテスト
│   ├── test_minimal.py         # 最小テスト例
│   └── test_timeout.py         # タイムアウトテスト例
├── flake.nix                   # Nix Flake定義
└── README.md                   # このファイル
```

## 提供する環境

- **Python 3.12**: ベース実行環境
- **pytest**: テストフレームワーク
- **pytest-json-report**: テスト結果JSON出力
- **pyright**: 型チェッカー
- **ruff**: リンター/フォーマッター

## Vesselツール

セキュアなPythonツール実行環境（Vessel）を提供：

### vessel-pyright
Pyright専用の実行環境。標準入力からPythonスクリプトを受け取り、pyrightコマンドを安全に実行。

```bash
echo 'result = safe_run_pyright(["--version"]); print(result["stdout"])' | nix run .#vessel-pyright
```

### vessel-python
Python/pytest/ruff統合実行環境。標準入力からPythonスクリプトを受け取り、各ツールを安全に実行。

```bash
echo 'result = safe_run_pytest(["--version"]); print(result["stdout"])' | nix run .#vessel-python
```

## 使用方法

### 1. 子プロジェクトでの参照

flake.nixで以下のように参照：

```nix
{
  inputs.python-flake.url = "path:/home/nixos/bin/src/flakes/python";
  
  outputs = { self, python-flake, ... }: {
    devShells.default = pkgs.mkShell {
      buildInputs = [
        python-flake.packages.${system}.pythonEnv
        python-flake.packages.${system}.pyright
        python-flake.packages.${system}.ruff
      ];
    };
  };
}
```

### 2. Pythonモジュールとしての使用

```python
from mod import (
    safe_run_pyright,
    validate_pyright_output,
    get_tool_config,
)

# Pyrightを実行
result = safe_run_pyright(["test.py"])
if result.get("success"):
    # 出力を検証
    analysis = validate_pyright_output(result["stdout"])
    if not analysis["valid"]:
        print(f"Found {analysis['summary']['error_count']} errors")
```

## 環境変数

以下の環境変数で動作をカスタマイズ可能：

- `PYTHON_TOOL_TIMEOUT`: ツール実行タイムアウト（秒、デフォルト: 60）
- `PYTHON_ALLOWED_TOOLS`: 許可するツール（カンマ区切り、デフォルト: pytest,ruff,pyright）
- `PYTHON_MAX_OUTPUT_SIZE`: 最大出力サイズ（文字数、デフォルト: 1048576）
- `PYTHON_PYRIGHT_VERSION`: 使用するpyrightバージョン（オプション）
- `PYTHON_RUFF_VERSION`: 使用するruffバージョン（オプション）

## セキュリティ

Vesselツールは以下のセキュリティ制限を適用：

- `eval`、`exec`、`__import__`の使用禁止
- `os.system`、`subprocess`の直接呼び出し禁止
- ファイル操作（`open`）の禁止
- ディレクトリトラバーサルの防止
- 許可されたツールのみ実行可能

## 開発

```bash
# 開発環境に入る
nix develop

# テストを実行
pytest tests/

# 利用可能なコマンドを表示
nix run

# READMEを表示
nix run .#readme
```

## 例

詳細な使用例は`examples/`ディレクトリを参照してください：

- `check_types.py`: Pyrightによる型チェック
- `combined_analysis.py`: 複数ツールの統合分析
- `lint_and_fix.py`: Ruffによるリンティングと自動修正
- `test_and_report.py`: Pytestによるテスト実行とレポート生成