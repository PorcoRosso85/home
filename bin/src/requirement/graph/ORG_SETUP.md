# /org 共有DB設定ガイド

## 概要

複数のClaudeインスタンスが同じデータベースを共有して作業するための設定方法。

## 環境変数設定

### 1. 必須環境変数

```bash
# 基本設定（すべてのインスタンスで必須）
export LD_LIBRARY_PATH="/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/"
export RGL_DB_PATH="/home/nixos/.rgl/default.db"  # デフォルトDB（単独実行用）
```

### 2. /org用共有DB設定

```bash
# /orgモード有効化
export RGL_ORG_MODE="true"

# 共有DBパス（すべてのインスタンスで同じパスを指定）
export RGL_SHARED_DB_PATH="/home/nixos/.rgl/shared_org.db"

# スキーマチェックスキップ（2回目以降）
export RGL_SKIP_SCHEMA_CHECK="true"
```

## /org実行時の設定

### 1. Worktree作成時の環境変数設定

```bash
# /orgコマンド内で各worktreeに環境変数を伝播
SHARED_ENV="LD_LIBRARY_PATH=$LD_LIBRARY_PATH RGL_DB_PATH=$RGL_DB_PATH RGL_ORG_MODE=true RGL_SHARED_DB_PATH=$GIT_ROOT/.rgl/shared_org.db"

# Claude起動時
nix run github:NixOS/nixpkgs/nixos-unstable#deno -- run --allow-all \
  "$CLAUDE_SDK_PATH" \
  --claude-id "$TASK-$TIMESTAMP" \
  --uri "$WORKTREE_PATH" \
  --allow-write \
  --env "$SHARED_ENV" \
  --print "$TASK_PROMPT" &
```

### 2. 初回DB作成

```bash
# 共有DBディレクトリ作成
mkdir -p $(dirname $RGL_SHARED_DB_PATH)

# スキーマ適用（初回のみ）
cd /home/nixos/bin/src/requirement/graph
$SHARED_ENV python -m infrastructure.apply_ddl_schema
```

### 3. 各ペルソナでの使用例

```python
# test_pm_simulation.py
import os
from infrastructure.variables.env import load_environment
from infrastructure.kuzu_repository_v2 import create_kuzu_repository

# 環境設定をロード
env_config = load_environment()

# 共有DBを使用するリポジトリを作成
repo = create_kuzu_repository(env_config)

# PMの要件を追加
pm_requirements = [
    {
        "ID": "pm_ux_001",
        "Title": "レスポンスタイム300ms以内",
        "Priority": 200,
        "CreatedBy": "ProductManager",
        "Metadata": {"metric": "response_time", "value": 300, "unit": "ms"}
    }
]

# 共有DBに保存
for req in pm_requirements:
    repo["save"](req)

# 他のペルソナの要件を確認（/orgモード時のみ）
shared_reqs = repo["get_shared_requirements"]()
print(f"共有DB内の要件数: {len(shared_reqs)}")
```

## 矛盾検出の実行

```python
# 統合検証（すべてのペルソナの要件を対象）
from application.integrated_consistency_validator import IntegratedConsistencyValidator

# 共有DBから全要件を取得
all_requirements = repo["get_shared_requirements"]()

# ペルソナごとにグループ化
pm_reqs = [r for r in all_requirements if r["created_by"] == "ProductManager"]
exec_reqs = [r for r in all_requirements if r["created_by"] == "Executive"]
eng_reqs = [r for r in all_requirements if r["created_by"] == "Engineer"]

# 統合検証実行
validator = IntegratedConsistencyValidator()
report = validator.validate_all(all_requirements)

print(f"検出された矛盾:")
print(f"- 意味的矛盾: {len(report['semantic_conflicts'])}")
print(f"- リソース競合: {len(report['resource_conflicts'])}")
print(f"- 優先度問題: {len(report['priority_issues'])}")
print(f"健全性スコア: {report['overall_health_score']}")
```

## トラブルシューティング

### 1. DBパスが異なる場合

```bash
# 各インスタンスで確認
echo "DB Path: $(python -c "from infrastructure.variables.env import load_environment, get_db_path; print(get_db_path(load_environment()))")"
```

### 2. スキーマエラーの場合

```bash
# スキーマを再適用
export RGL_SKIP_SCHEMA_CHECK="false"
python -m infrastructure.apply_ddl_schema
```

### 3. 環境変数の確認

```bash
# 必須環境変数チェック
python -c "from infrastructure.variables.env import load_environment; print(load_environment())"
```

## まとめ

1. `RGL_ORG_MODE=true` で共有DBモードを有効化
2. `RGL_SHARED_DB_PATH` で共有DBパスを指定
3. すべてのインスタンスで同じ環境変数を設定
4. `get_shared_requirements()` で全ペルソナの要件を取得
5. 統合バリデーターで矛盾を検出