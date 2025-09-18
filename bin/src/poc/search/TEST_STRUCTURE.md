# POC Search テスト構造

## テストの階層と目的

### 1. 仕様テスト（Specification Tests）
**ファイル**: `test_kuzu_native_spec.py`
- **目的**: 実装すべき機能の仕様を明確化
- **特徴**: 
  - `@pytest.mark.skip`で未実装を明示
  - 仕様をコメントで詳細記述
  - 必要な機能を列挙

### 2. 統合テスト（Integration Tests）
**ファイル**: `test_requirement_search_integration.py`
- **目的**: KuzuDBネイティブ機能の動作確認
- **特徴**:
  - 実際のVSS/FTS機能をテスト
  - 最小限のテストデータで検証
  - 拡張機能が利用できない場合はスキップ

### 3. E2Eテスト（End-to-End Tests）
**ファイル**: `test_hybrid_search_e2e.py`
- **目的**: 実際のユースケースでの動作確認
- **特徴**:
  - 要件管理の実シナリオ
  - ビジネス価値の検証
  - ユーザー視点での動作確認

## 削除したテスト

以下のテストは無意味なため削除：
- `test_hybrid_search.py` - assert Trueのみ
- `test_collaborative_requirements.py` - assert Trueのみ
- `test_hybrid_complete.py` - E2Eテストに統合

## テスト実行方法

```bash
# 仕様テストの確認（スキップされるテストを含む）
pytest test_kuzu_native_spec.py -v

# 統合テストの実行
pytest test_requirement_search_integration.py -v

# E2Eシナリオの実行
python test_hybrid_search_e2e.py
```

## テスト設計の原則

1. **無意味なテストを書かない**
   - assert Trueだけのテストは削除
   - 実装の見込みがないテストは削除

2. **仕様を明確にする**
   - 未実装でも仕様は記述
   - skipで実装待ちを明示

3. **実用的なシナリオ**
   - 実際の要件管理での課題を解決
   - ビジネス価値を検証

4. **KuzuDBネイティブ機能**
   - モック実装は最小限
   - 実際の拡張機能を使用