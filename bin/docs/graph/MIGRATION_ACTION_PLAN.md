# Architecture移行アクションプラン

## エグゼクティブサマリー

Flake Graph Explorerのarchitecture/{dml,dql}への移行準備が65%完了。コア機能は実装済みだが、統合層の改善が必要。

## 完了した準備作業

### ✅ Step 1: グラフエッジ構築機能
- `graph_edge_builder.py`実装完了
- flake.nix依存関係の解析とDEPENDS_ONエッジ作成
- テストはGREEN（基本機能動作確認）

### ✅ Step 2: 重複検出結果の永続化
- `duplicate_relation_writer.py`実装完了
- DUPLICATES_WITH関係のグラフDB永続化
- 完全グラフ構造での重複グループ表現

### ✅ Step 3: VSS検索のDQL/DML分離戦略
- DML: エンベディング生成・永続化
- DQL: Cypherクエリでの検索
- 分離アーキテクチャの明確化

### ✅ Step 4: DQL Cypherテンプレート作成
- 13個のCypherファイル作成（architecture/dql/）
- 実装固有のクエリテンプレート定義

## 残作業と推奨アクション

### 🔴 Phase 1: 統合層の修正（1週間）

#### 1.1 KuzuAdapterの統合問題修正
```python
# 現状: GraphEdgeBuilderがKuzuAdapterなしで作成される
builder = GraphEdgeBuilder()  # ❌

# 修正: 適切な依存性注入
kuzu_adapter = create_kuzu_adapter(db_path)
builder = GraphEdgeBuilder(kuzu_adapter)  # ✅
```

#### 1.2 VSSデータ構造の統一
```python
# 現状: search結果にidフィールドがない
result = {"path": "/src/foo", "similarity": 0.9}  # ❌

# 修正: 一貫したデータ構造
result = {"id": "foo", "path": "/src/foo", "similarity": 0.9}  # ✅
```

### 🟡 Phase 2: DML機能の完成（1週間）

#### 2.1 エンベディング生成モジュール
```
architecture/dml/implementation/embeddings/
├── embedding_generator.py    # 新規作成必要
├── incremental_processor.py  # 新規作成必要
└── batch_processor.py       # 新規作成必要
```

#### 2.2 サービス層の実装
```
architecture/dml/implementation/application/
├── scan_service.py          # スキャンのオーケストレーション
├── embedding_service.py     # エンベディング管理
└── analysis_service.py      # 分析結果の統合
```

### 🟢 Phase 3: 移行実施（3日）

#### 3.1 ディレクトリ構造の作成
```bash
mkdir -p architecture/dml/implementation/{scanner,analyzers,embeddings,infrastructure,domain,application}
```

#### 3.2 コードの移動とリファクタリング
1. 既存コードを新しい構造にコピー
2. import pathの更新
3. 統合テストの実行

#### 3.3 旧コードの削除
- 動作確認後、bin/docs/graph/の旧実装を削除

## リスクと対策

### リスク1: KuzuDB VECTOR拡張の互換性
**対策**: 
- 移行前にVECTOR拡張の動作確認テスト実施
- フォールバック戦略の準備

### リスク2: パフォーマンス劣化
**対策**:
- ベンチマークテストの実施
- 段階的な移行で性能監視

### リスク3: 既存機能の破壊
**対策**:
- 包括的な統合テストスイート
- カナリアリリース戦略

## 成功指標

1. **機能完全性**: すべての既存テストがGREEN
2. **パフォーマンス**: 起動時間90%削減の達成
3. **アーキテクチャ**: DML/DQLの完全分離
4. **保守性**: 各モジュールの独立テスト可能性

## タイムライン

```
Week 1: 統合層の修正とテスト
Week 2: DML機能の完成
Week 3: 移行実施と検証
```

## 結論

architecture移行の技術的基盤は整っている。統合層の改善と残りのDML機能実装により、3週間での移行完了が可能。