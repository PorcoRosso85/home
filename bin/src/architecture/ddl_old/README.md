# DDL管理ディレクトリ

このディレクトリは、アーキテクチャGraph DBのスキーマ定義を管理します。

## 設計原則

1. **モジュラー設計**: ノードとエッジを分離して管理
2. **バージョン管理**: マイグレーションによる段階的スキーマ進化
3. **自動統合**: 個別定義から統合スキーマを自動生成

## ディレクトリ構造

```
ddl/
├── core/                      # コアスキーマ定義
│   ├── nodes/                # ノードテーブル定義
│   │   ├── requirement.cypher    # 要件エンティティ
│   │   ├── location.cypher       # ロケーションURI
│   │   └── version.cypher        # バージョン状態
│   └── edges/                # エッジテーブル定義
│       ├── locates.cypher        # LOCATES関係
│       ├── tracks_state.cypher   # TRACKS_STATE_OF関係
│       └── depends_on.cypher     # DEPENDS_ON関係
├── migrations/               # スキーママイグレーション
│   └── v4.0.0_architecture_base.cypher
└── schema.cypher            # 統合スキーマ（自動生成）
```

## requirement/graphとの関係

- **独立性**: requirement/graphのDDLから完全に独立
- **互換性**: 既存スキーマとの互換性を維持
- **拡張性**: アーキテクチャ固有の拡張を追加可能

## スキーマ生成プロセス

1. `core/nodes/`と`core/edges/`の個別定義を作成
2. `infrastructure/schema_manager.py`で統合スキーマを生成
3. `migrations/`でバージョン管理