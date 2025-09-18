# FTS vs VSS API構造比較分析

## 概要
FTS (Full-Text Search) とVSS (Vector Similarity Search) のAPI構造を比較し、統一化のための改善点を特定します。

## 1. 現在のAPI構造比較

### FTS API (リファクタリング後)
```python
# シンプルな関数ベースAPI
from fts_kuzu import (
    create_fts_connection,    # 接続作成の簡易関数
    index_fts_documents,      # ドキュメントインデックスの簡易関数
    search_fts_documents,     # 検索の簡易関数
)

# 使用例
connection = create_fts_connection(in_memory=True)
result = index_fts_documents(documents, connection)
search_result = search_fts_documents({"query": "検索語"}, connection)
```

### VSS API (現在)
```python
# 高階関数による複雑なサービス作成
from vss_kuzu import (
    create_vss_service,       # 高階関数でサービスを作成
    create_embedding_service, # 埋め込み生成サービス
    # 個別のインフラ関数群
    create_kuzu_database,
    create_kuzu_connection,
    check_vector_extension,
    initialize_vector_schema,
    insert_documents_with_embeddings,
    search_similar_vectors,
)

# 使用例（複雑）
# 1. 各種関数を個別に準備
embedding_func = create_embedding_service("model_name")
db_config = DatabaseConfig(...)
success, database, error = create_kuzu_database(db_config)
success, connection, error = create_kuzu_connection(database)

# 2. サービスを作成
vss_funcs = create_vss_service(
    create_db_func=create_kuzu_database,
    create_conn_func=create_kuzu_connection,
    # ... 10個の関数を渡す
)

# 3. 使用
result = vss_funcs["index_documents"](documents, config)
```

## 2. 主要な差分

### 2.1 API設計思想
| 項目 | FTS | VSS |
|------|-----|-----|
| 設計アプローチ | シンプルな関数 | 高階関数による DI |
| 関数の粒度 | 高レベル（統合済み） | 低レベル（要組み立て） |
| 使いやすさ | 簡単（3関数で完結） | 複雑（多数の関数を組み合わせ） |
| 柔軟性 | 中程度 | 高い |

### 2.2 関数命名規則
| 操作 | FTS | VSS |
|------|-----|-----|
| 接続作成 | `create_fts_connection()` | なし（個別関数を組み合わせ） |
| インデックス | `index_fts_documents()` | `vss_funcs["index_documents"]()` |
| 検索 | `search_fts_documents()` | `vss_funcs["search"]()` |

### 2.3 パラメータ形式
| 項目 | FTS | VSS |
|------|-----|-----|
| 設定 | `ApplicationConfig` (内部) | `ApplicationConfig` + `VSSConfig` |
| 埋め込み | なし（FTSは不要） | 外部から注入 |
| 接続管理 | 関数内で自動管理 | ユーザーが管理 |

### 2.4 戻り値形式
両方とも統一された形式を使用:
```python
# 成功時
{"ok": True, "results": [...], "metadata": {...}}

# エラー時
{"ok": False, "error": "...", "details": {...}}
```

## 3. VSS APIの改善提案

### 3.1 シンプルなラッパー関数の追加
FTSと同様の使いやすいAPI関数を追加:

```python
# 新しいVSS API（FTSと統一）
def create_vss_connection(
    db_path: str = "./kuzu_db",
    in_memory: bool = False,
    model_name: str = "ruri-v3-30m"
) -> Dict[str, Any]:
    """VSS用の接続を簡単に作成"""
    pass

def index_vss_documents(
    documents: List[Dict[str, str]],
    connection: Any = None,
    config: ApplicationConfig = None
) -> Dict[str, Any]:
    """ドキュメントを簡単にインデックス"""
    pass

def search_vss_documents(
    search_input: Dict[str, Any],
    connection: Any = None,
    config: ApplicationConfig = None
) -> Dict[str, Any]:
    """簡単に類似検索を実行"""
    pass
```

### 3.2 API使用パターンの統一

#### 現在のVSS（複雑）
```python
# 10個以上の関数をインポート
# 手動でサービスを組み立て
# 埋め込み関数を別途準備
```

#### 改善後のVSS（FTSと同様）
```python
# 3つの主要関数のみ
conn_info = create_vss_connection(in_memory=True)
result = index_vss_documents(documents, conn_info["connection"])
search_result = search_vss_documents({"query": "検索語"}, conn_info["connection"])
```

### 3.3 実装アプローチ
1. 既存の高階関数アーキテクチャは保持（柔軟性のため）
2. 新しいシンプルなラッパー関数を追加
3. デフォルトの埋め込みモデルを内部で自動設定
4. 接続管理を自動化

## 4. 移行計画

### Phase 1: VSS簡易API関数の追加
- `create_vss_connection()` 実装
- `index_vss_documents()` 実装  
- `search_vss_documents()` 実装

### Phase 2: テストの追加
- 新しいAPI関数のテスト作成
- FTSと同様の使用パターンを確認

### Phase 3: ドキュメント更新
- READMEに新しい簡易APIの使用例を追加
- 高度な使用例は別セクションに移動

### Phase 4: エクスポートの更新
- `__init__.py`に新関数を追加
- 主要APIとして位置づけ

## 5. 利点

### 呼び出し側の利点
1. **学習コスト削減**: FTSとVSSで同じパターンを使用
2. **実装の簡素化**: 3関数で基本操作が完結
3. **エラー削減**: 複雑な設定が不要
4. **移行の容易さ**: FTSからVSSへの切り替えが簡単

### 保守性の向上
1. **API一貫性**: 両ライブラリで統一されたインターフェース
2. **テスト容易性**: シンプルなAPIはテストも簡単
3. **ドキュメント統一**: 同じパターンで説明可能

## 6. 後方互換性
- 既存の高階関数APIは維持
- 新しい簡易APIは内部で高階関数を使用
- 段階的な移行が可能