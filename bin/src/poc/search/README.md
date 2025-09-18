# POC Search - KuzuDB VSS/FTS/Hybrid Search

## 目的

KuzuDBのネイティブ機能（VSS/FTS/Graph）を活用した、
高度な要件管理システムの検索機能を実証するPOCです。

## 主要機能

1. **重複要件検出**: 複数チーム間での重複定義を自動検出
2. **影響分析**: 要件変更時の影響範囲を包括的に分析
3. **用語統一**: プロジェクト全体での用語一貫性を保証

### 厳格なルール
1. **KuzuDB拡張機能のみ使用**
   - VSS: `CREATE_VECTOR_INDEX`, `QUERY_VECTOR_INDEX`
   - FTS: `CREATE_FTS_INDEX`, `QUERY_FTS_INDEX`
2. **手動実装禁止**
   - Pythonでのコサイン類似度計算 ❌
   - 全件スキャンによる類似検索 ❌
   - フォールバック実装 ❌
3. **複数人協調を前提**
   - 並行編集の競合検出
   - ゴール整合性の維持
   - 用語統一性の確保

## テスト実行

```bash
# 仕様テストの確認
pytest test_search_poc_spec.py -v

# 統合テストの実行
pytest test_kuzu_vss_fts_integration.py -v -s

# E2Eシナリオの実行
python test_hybrid_search_e2e.py

# 全テスト実行
nix run .#test
```

## 成功基準

- 重複検出率: > 90%
- 検索精度: > 85%
- レスポンス時間: < 100ms

## 関連ドキュメント

- [TEST_STRUCTURE.md](TEST_STRUCTURE.md) - テスト構造の詳細
- [SEARCH_POC_ARCHITECTURE.md](SEARCH_POC_ARCHITECTURE.md) - アーキテクチャ詳細
- [KUZUDB_VSS_SPEC.md](vss/KUZUDB_VSS_SPEC.md) - KuzuDB VSS拡張機能仕様
- [KUZUDB_FTS_SPEC.md](fts/KUZUDB_FTS_SPEC.md) - KuzuDB FTS拡張機能仕様

## テスト構造

### 仕様テスト（実行可能なドキュメント）
- `test_search_poc_spec.py` - POCの全体仕様と期待される振る舞い
- `test_kuzu_native_spec.py` - KuzuDBネイティブ機能の仕様

### 統合テスト（実装例）
- `test_kuzu_vss_fts_integration.py` - VSS/FTS機能の最小実装
- `test_requirement_search_integration.py` - 要件検索の動作確認

### E2Eテスト（シナリオ検証）
- `test_hybrid_search_e2e.py` - 実際のユースケースでの検証

詳細は[TEST_STRUCTURE.md](TEST_STRUCTURE.md)を参照してください。

## アーキテクチャ

詳細は[SEARCH_POC_ARCHITECTURE.md](SEARCH_POC_ARCHITECTURE.md)を参照してください。

### 主要コンポーネント

1. **VSS (Vector Similarity Search)**
   - 384次元埋め込みベクトル
   - HNSWアルゴリズム
   - 意味的類似度検索

2. **FTS (Full-Text Search)**
   - 日本語トークナイズ対応
   - キーワードベース検索
   - TF-IDFスコアリング

3. **Graph Traversal**
   - 依存関係の探索
   - 影響範囲の特定
   - 循環参照検出

## 実装要件

### 厳格なルール
1. **KuzuDB拡張機能のみ使用**
   - VSS: `CREATE_VECTOR_INDEX`, `QUERY_VECTOR_INDEX`
   - FTS: `CREATE_FTS_INDEX`, `QUERY_FTS_INDEX`
2. **手動実装禁止**
   - Pythonでのコサイン類似度計算 ❌
   - 全件スキャンによる類似検索 ❌
   - フォールバック実装 ❌