# アプリケーション層

[ドメインルール](../domain/README.md)に基づく操作可能なユースケースを定義。

## 現在の状態

Phase 1により大幅に機能を削減。残存する主要機能：
- エラーハンドリング（error_handler.py）

削除した機能：
- 摩擦スコアリング系バリデータ（5ファイル）
- バージョンサービス（2ファイル）

## 今後の統合予定

### Phase 2: テンプレート体系
入力の標準化と検証を保証する操作定義。

### Phase 3: Search Service統合
重複チェックを伴う要件の新規作成。類似要件が存在する場合は通知。

## SearchAdapter - 接続共有

SearchAdapterは`repository_connection`パラメータを通じて既存のKuzuDB接続を再利用できます。

### 使用方法

```python
from kuzu import Database
from requirement.graph.application.search_adapter import SearchAdapter

# 既存の接続を作成
db = Database("path/to/db")
conn = db.connect()

# 接続を共有してSearchAdapterを初期化
adapter = SearchAdapter(
    db_path="path/to/db",
    repository_connection=conn  # 既存接続を渡す
)
```

### 接続共有の利点

1. **パフォーマンス向上**: 新規接続の作成コストを削減
2. **一貫性の保証**: 同一トランザクション内での操作が可能
3. **リソース効率**: データベース接続数の削減

### 使用シナリオ

- **接続共有を推奨**: アプリケーション全体で単一の接続を管理する場合
- **新規接続を推奨**: 独立したタスクや並行処理を行う場合

## フィードバックループ

1. **提案**: テンプレート+パラメータで操作を要求（Phase 2で実装予定）
2. **評価**: ドメインルールと類似検索による検証（Phase 3で実装予定）
3. **改善**: フィードバックに基づく修正

## 下位層との協調

[`infrastructure層`](../infrastructure/README.md)の技術基盤を利用してユースケースを実現。