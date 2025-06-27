# テスト実行ガイド

requirement/graphプロジェクトのin-sourceテスト実行方法

## 概要

本プロジェクトは規約(CONVENTION.yaml)に従い、すべてのテストをin-source（実装ファイル内）に記述しています。

**重要**: テストの実行は`uv run`コマンドのみで行います。

## テスト実行方法

### uvコマンドによる実行（唯一の方法）

```bash
# 全テスト実行
uv run pytest

# 詳細出力
uv run pytest -v

# 特定ディレクトリのみ
uv run pytest infrastructure/

# キーワード指定
uv run pytest -k "階層違反"

# 特定ファイル
uv run pytest infrastructure/hierarchy_validator.py

# 特定のテスト関数
uv run pytest infrastructure/requirement_validator.py::test_曖昧な表現_速い_エラーと改善提案
```

### 環境変数

環境変数は`conftest.py`で自動設定されます：
- `LD_LIBRARY_PATH`: KuzuDB用ライブラリパス
- `RGL_DB_PATH`: データベースファイルパス

## テスト作成ガイドライン

### pytest形式（必須）

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

### 禁止事項

- `if __name__ == "__main__"`ブロック
- `unittest.main()`の使用
- 独自のテストランナー
- pytest以外のテストフレームワーク

## プロジェクト設定

### pyproject.toml

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["."]
python_files = ["*.py"]
python_functions = ["test_*"]
```

### conftest.py

自動的に以下を設定：
- 環境変数
- テスト収集時の除外ファイル
- カスタムフィクスチャ

## トラブルシューティング

### uvコマンドが見つからない

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### ImportError

`conftest.py`が環境変数を自動設定するため、通常は発生しません。

### テストが見つからない

in-sourceテストは`test_`で始まる関数名が必要です。