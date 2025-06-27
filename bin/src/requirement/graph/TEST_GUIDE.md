# テスト実行ガイド

requirement/graphプロジェクトのin-sourceテスト実行方法

## 概要

本プロジェクトは規約(CONVENTION.yaml)に従い、すべてのテストをin-source（実装ファイル内）に記述しています。

## テスト実行方法

### 1. pytest（推奨）

```bash
# 全テスト実行
bash run_pytest.sh

# 詳細出力
bash run_pytest.sh -v

# 特定ディレクトリのみ
bash run_pytest.sh infrastructure/

# キーワード指定
bash run_pytest.sh -k "階層違反"

# 特定ファイル
bash run_pytest.sh infrastructure/hierarchy_validator.py
```

**メリット:**
- パラメータ化テスト
- フィクスチャ
- より良いエラーレポート
- 部分実行が容易

### 2. unittest形式（pytest未インストール時）

```bash
# 全テスト実行
python run_all_tests_with_env.py

# 個別モジュール実行
LD_LIBRARY_PATH=/nix/store/1n4957f86zjh8gv7j8a1ga1gx35naqqk-gcc-12.3.0-lib/lib \
RGL_DB_PATH=./rgl_db \
python -m requirement.graph.infrastructure.hierarchy_validator test
```

## テスト作成ガイドライン

### pytest形式（新規推奨）

```python
import pytest

def test_シンプルなテスト():
    """関数形式のテスト"""
    assert 1 + 1 == 2

class TestMyFeature:
    """クラス形式のテスト"""
    
    @pytest.fixture
    def setup_data(self):
        return {"key": "value"}
    
    def test_with_fixture(self, setup_data):
        assert setup_data["key"] == "value"
    
    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
    ])
    def test_parameterized(self, input, expected):
        assert input * 2 == expected
```

### unittest形式（後方互換性）

```python
import unittest

def test_関数形式():
    """unittest.main()で実行される"""
    assert True

if __name__ == "__main__":
    unittest.main()
```

## 環境変数

以下の環境変数が必要です（run_pytest.shで自動設定）：

- `LD_LIBRARY_PATH`: KuzuDB用ライブラリパス
- `RGL_DB_PATH`: データベースファイルパス

## テスト統計（2024年現在）

- 総テスト数: 119個
- pytest成功率: 86%（102/119）
- 主要モジュール:
  - hierarchy_validator.py: 12テスト
  - requirement_validator.py: 13テスト
  - main.py: 3テスト（DB統合テスト含む）

## トラブルシューティング

### ImportError
環境変数が設定されていません。run_pytest.shを使用してください。

### pytest not found
仮想環境をアクティベートしてください：
```bash
source /home/nixos/bin/src/.venv/bin/activate
```

### テストが見つからない
in-sourceテストは`test_`で始まる関数名が必要です。