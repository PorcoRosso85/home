# Contract Service KuzuDB統合指示書

本文書は、Contract ServiceのDDLをKuzuDBと統合するための詳細な指示書です。
記憶が失われても実装可能なよう、すべての手順を明記します。

## 前提条件

- `/home/nixos/bin/docs/conventions/` の規約を厳守
- TDDプロセス（Red-Green-Refactor）を必須とする
- `bin/src/persistence/kuzu_py` の既存実装を活用
- TodoWrite/TodoReadツールで進捗管理

## DDL定義（最終版）

```cypher
-- ノードテーブル
CREATE NODE TABLE LocationURI (
    id STRING PRIMARY KEY
);

CREATE NODE TABLE App (
    id STRING PRIMARY KEY
);

CREATE NODE TABLE Schema (
    id STRING PRIMARY KEY,
    schema_content STRING,
    version STRING DEFAULT '1.0'
);

CREATE NODE TABLE VersionState (
    id STRING PRIMARY KEY,
    timestamp STRING,
    description STRING,
    change_reason STRING,
    operation STRING DEFAULT 'UPDATE',
    author STRING DEFAULT 'system'
);

-- エッジテーブル
CREATE REL TABLE LOCATES (
    FROM LocationURI TO App,
    entity_type STRING DEFAULT 'app',
    current BOOLEAN DEFAULT true
);

CREATE REL TABLE PROVIDES (
    FROM App TO Schema,
    schema_role STRING,      -- 'input' or 'output'
    active BOOLEAN DEFAULT true,
    since_timestamp STRING
);

CREATE REL TABLE EXPECTS (
    FROM App TO Schema,
    schema_role STRING,      -- 'input' or 'output'
    active BOOLEAN DEFAULT true,
    since_timestamp STRING
);

CREATE REL TABLE CAN_COMMUNICATE_WITH (
    FROM App TO App,
    transform_rules STRING,
    compatibility_score DOUBLE DEFAULT 1.0
);

CREATE REL TABLE TRACKS_STATE_OF (
    FROM VersionState TO LocationURI,
    entity_type STRING DEFAULT 'app'
);

CREATE REL TABLE CONTAINS_LOCATION (
    FROM LocationURI TO LocationURI
);
```

## 統合手順

### Phase 1: 最小統合確認

#### Step 1.1: DDLファイル作成
1. `/home/nixos/bin/src/poc/contract/ddl/` ディレクトリを作成
2. `contract_schema.cypher` ファイルを作成し、上記DDLを保存

#### Step 1.2: 失敗するテスト作成（RED）
```python
# test/integration/test_kuzu_integration.py
import pytest
from persistence.kuzu_py.core.database import create_database

def test_can_create_contract_tables():
    """契約テーブルが作成できることを確認"""
    # Arrange
    db = create_database(in_memory=True, use_cache=False)
    
    # Act - この時点では実装がないため失敗する
    with pytest.raises(Exception):
        # DDLを適用する処理（未実装）
        apply_ddl(db, "ddl/contract_schema.cypher")
    
    # Assert - テーブルの存在確認
    tables = db.execute("CALL table_info() RETURN *").get_as_df()
    assert "LocationURI" in tables["name"].values
```

#### Step 1.3: 最小実装（GREEN）
```python
# src/kuzu_integration.py
from pathlib import Path
from persistence.kuzu_py.core.database import create_database

def apply_ddl(db, ddl_path: str):
    """DDLファイルを適用"""
    ddl_file = Path(__file__).parent / ddl_path
    with open(ddl_file, 'r') as f:
        statements = f.read().split(';')
        for stmt in statements:
            if stmt.strip():
                db.execute(stmt.strip() + ';')
```

#### Step 1.4: リファクタリング（REFACTOR）
- エラーハンドリング追加
- ログ出力追加
- DDLSchemaManagerパターンの適用

### Phase 2: 基本操作の実装

#### Step 2.1: App登録テスト（RED）
```python
def test_register_provider_app():
    """Provider Appを登録できることを確認"""
    # Arrange
    db = create_database(in_memory=True, use_cache=False)
    apply_ddl(db, "ddl/contract_schema.cypher")
    
    # Act
    result = register_app(
        db,
        location_uri="http://weather:8080/v1",
        app_id="weather-service-v1"
    )
    
    # Assert
    assert result["status"] == "registered"
    assert result["app_id"] == "weather-service-v1"
```

#### Step 2.2: 実装（GREEN）
最小限の実装でテストを通す

#### Step 2.3: スキーマ登録、関係作成と続く

### Phase 3: 既存コードとの統合

1. `kuzu_wrapper.ts` のモック実装を実際のKuzuDB呼び出しに置換
2. `registry.ts` の実装をKuzuDB版に更新
3. `matcher.ts` のクエリを実際のCypherに変換

## 検証ポイント

### 最小統合の確認
1. DDLが正常に適用される
2. 基本的なCRUD操作が動作する
3. エラーハンドリングが適切

### パフォーマンス確認
1. インデックスの必要性を検証
2. クエリの実行計画を確認

### 既存機能との互換性
1. JSON-RPC APIが既存通り動作
2. テストケースがすべてパス

## 注意事項

1. **TDD厳守**: 必ずRED→GREEN→REFACTORの順序を守る
2. **段階的統合**: 一度にすべてを変更せず、小さなステップで進める
3. **ログ活用**: `bin/src/log/`のロギング規約に従う
4. **テスト実行**: `nix run .#test` でテストを必ず実行

## トラブルシューティング

### DDL適用エラー
- KuzuDBのバージョン確認
- Cypher構文の互換性確認

### パフォーマンス問題
- インデックス追加を検討
- クエリの最適化

### 既存コードとの不整合
- インターフェースアダプターパターンで解決

---

本指示書に従い、段階的に統合を進めてください。
各フェーズ完了時には必ずテストを実行し、品質を確保してください。