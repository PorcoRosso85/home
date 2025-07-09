# POC Search - KuzuDB VSS/FTS/Hybrid Search

## ディレクトリの責務

このディレクトリは**KuzuDBのネイティブVSS/FTS機能のみを使用**した要件検索の実装を担当します。

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
cd /home/nixos/bin/src/poc/search
nix run .#test
```

## テストファイル

### 基本機能テスト
- `test_hybrid_search.py` - ハイブリッド検索の基本6シナリオ

### 協調作業テスト（TDD Red）
- `test_collaborative_requirements.py` - 複数人協調のための7つのテスト
  - 並行編集の競合検出
  - ゴール整合性
  - 用語統一性
  - 循環依存検出
  - 要件完全性
  - 変更一貫性
  - 優先度整合性

## 実装要件

すべての検索はKuzuDBネイティブ機能で実装すること：
```python
# ✅ 正しい実装
conn.execute("CALL QUERY_VECTOR_INDEX(...)")
conn.execute("CALL QUERY_FTS_INDEX(...)")

# ❌ 禁止された実装
def calculate_cosine_similarity(vec1, vec2):  # 手動計算禁止
    pass
```