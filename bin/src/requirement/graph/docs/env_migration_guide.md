# 環境変数管理移行ガイド

## 移行の概要

外部変数管理を `env.py` に統一し、保守性を向上させます。

## 変更点

### 1. 削除されるファイル
- `env_vars.py` - env.py に統合
- `paths.py` - 環境変数ベースに変更（デフォルト値削除）

### 2. 新しいAPI

#### 必須環境変数
```python
# 旧
from infrastructure.variables import LD_LIBRARY_PATH

# 新（推奨）
from infrastructure.variables import get_ld_library_path
ld_path = get_ld_library_path()
```

#### DB パス取得（/org モード対応）
```python
from infrastructure.variables import get_db_path
db_path = get_db_path()  # 自動的に /org モードを検出
```

#### 環境検証
```python
from infrastructure.variables import validate_environment
errors = validate_environment()
if errors:
    print("環境設定エラー:", errors)
```

### 3. 規約遵守

- **デフォルト値禁止**: すべての外部変数は明示的に設定が必要
- **関数経由アクセス**: グローバル変数ではなく関数で取得
- **エラーハンドリング**: 必須変数が未設定の場合は EnvironmentError

### 4. テスト

```python
def test_with_env(monkeypatch):
    monkeypatch.setenv("LD_LIBRARY_PATH", "/test/lib")
    monkeypatch.setenv("RGL_DB_PATH", "/test/db")
    
    # テストコード
```

## 移行手順

1. インポートを更新（変数→関数）
2. デフォルト値に依存しているコードを修正
3. 環境変数を明示的に設定
4. テストを実行