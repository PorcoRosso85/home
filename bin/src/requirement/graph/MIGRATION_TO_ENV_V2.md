# 環境変数管理v2への移行計画

## 概要

既存の環境変数管理を規約準拠の新システムに移行する。

## 移行対象

### 1. 削除予定ファイル
- `infrastructure/variables/env_vars.py` - デフォルト値使用（規約違反）
- `infrastructure/variables/paths.py` - デフォルト値使用（規約違反）

### 2. 新規ファイル
- `infrastructure/variables/env.py` - 規約準拠の環境変数管理

### 3. 更新が必要なファイル

```python
# main.py
# 変更前
from .infrastructure.variables import get_db_path

# 変更後
from .infrastructure.variables.env import load_environment, get_db_path
env_config = load_environment()
db_path = get_db_path(env_config)
```

```python
# kuzu_repository.py → kuzu_repository_v2.py
# 変更前
def create_kuzu_repository(db_path: str = None):
    if db_path is None:
        db_path = get_db_path()  # 環境変数から直接取得

# 変更後
def create_kuzu_repository(env_config: Optional[Dict] = None):
    if env_config is None:
        env_config = load_environment()
    db_path = get_db_path(env_config)
```

## 移行手順

### Phase 1: 並行運用（現在）
1. 新システム（env.py）を作成 ✓
2. kuzu_repository_v2.py を作成 ✓
3. ORG_SETUP.md でドキュメント化 ✓

### Phase 2: 段階的移行
1. テストコードから新システムを使用開始
2. CLI関連コードを更新
3. main.pyを更新

### Phase 3: 完全移行
1. 旧ファイルを削除
2. インポートパスを統一
3. ドキュメント更新

## 互換性維持策

```python
# infrastructure/variables/__init__.py で一時的な互換性を提供
try:
    # 新システムを優先
    from .env import load_environment, get_db_path as _get_db_path
    
    # 旧インターフェース（非推奨）
    def get_db_path():
        """@deprecated Use load_environment() and get_db_path(config) instead"""
        config = load_environment()
        return _get_db_path(config)
        
except ImportError:
    # フォールバック（移行期間中のみ）
    from .env_vars import get_db_path
```

## 影響を受けるコンポーネント

| コンポーネント | 現在の依存 | 移行後の依存 | 優先度 |
|-------------|-----------|------------|--------|
| main.py | env_vars.get_db_path() | env.load_environment() | 高 |
| kuzu_repository.py | env_vars全般 | env.load_environment() | 高 |
| cli_adapter.py | paths.get_default_* | env.load_environment() | 中 |
| テストコード | 直接os.environ設定 | env_configを注入 | 中 |
| logger.py | env_vars.get_log_level() | env.load_environment() | 低 |

## テスト戦略

```python
# test_env_migration.py
import pytest
from infrastructure.variables.env import load_environment

class TestEnvMigration:
    def test_required_env_vars(self, monkeypatch):
        """必須環境変数のテスト"""
        monkeypatch.setenv("LD_LIBRARY_PATH", "/test/lib")
        monkeypatch.setenv("RGL_DB_PATH", "/test/db")
        
        config = load_environment()
        assert config["ld_library_path"] == "/test/lib"
        assert config["rgl_db_path"] == "/test/db"
    
    def test_org_mode_db_resolution(self, monkeypatch):
        """/orgモードでのDB解決"""
        monkeypatch.setenv("LD_LIBRARY_PATH", "/test/lib")
        monkeypatch.setenv("RGL_DB_PATH", "/local/db")
        monkeypatch.setenv("RGL_SHARED_DB_PATH", "/shared/db")
        monkeypatch.setenv("RGL_ORG_MODE", "true")
        
        config = load_environment()
        db_path = get_db_path(config)
        
        assert db_path == "/shared/db"
```

## リスクと対策

### リスク1: 既存環境での動作不良
**対策**: 互換性レイヤーを提供し、段階的に移行

### リスク2: 環境変数の設定ミス
**対策**: 明確なエラーメッセージとセットアップガイド

### リスク3: テストの失敗
**対策**: テスト用のenv_config注入機能を提供

## 完了基準

- [ ] すべてのコンポーネントが新システムを使用
- [ ] 旧ファイル（env_vars.py, paths.py）を削除
- [ ] ドキュメントを更新
- [ ] /orgモードでの共有DB動作確認
- [ ] すべてのテストがグリーン