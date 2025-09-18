# FTS Flake要件とテスト仕様化の分析

## 1. Flakeの意義・要件

### Flake.nixから読み取れる要件
1. **目的**: "FTS (Full-Text Search) with KuzuDB" - KuzuDBを使用したフルテキスト検索
2. **バージョン**: 0.2.0 (VSSからの進化版)
3. **コア依存関係**:
   - kuzu/kuzu_py: グラフデータベース統合
   - numpy: 数値計算（BM25スコアリング等）
4. **開発環境**: pytest, ruff, black による品質管理
5. **標準化コマンド**: `nix run .#test/lint/format`

## 2. テストによる仕様化の評価

### ✅ 適切に仕様化されている要件

#### アプリケーション層テスト（test_application.py）
- **FTSの基本動作**:
  - `test_indexing_documents_with_distinct_ids_stores_separately`: 文書の個別保存
  - `test_indexed_documents_are_searchable_immediately`: 即座の検索可能性
  - `test_keyword_search_returns_matching_documents`: キーワード検索機能

- **FTS特有の機能**:
  - `test_case_insensitive_search`: 大文字小文字を区別しない検索
  - `test_multi_word_query_searches_all_words`: 複数単語クエリのサポート
  - `test_search_results_include_score_and_highlights`: スコアとハイライト

- **エラーハンドリング**:
  - `test_missing_query_returns_error`: 必須パラメータの検証
  - `test_successful_and_error_responses_follow_consistent_structure`: 一貫したレスポンス構造

#### ドメイン層テスト（test_domain.py）
- **BM25スコアリング**:
  - `test_bm25_scoring_ranks_documents_by_relevance`: BM25による関連性ランキング
  - `test_search_results_include_position_highlights`: 位置情報付きハイライト

- **高度な検索機能**:
  - `test_phrase_search_finds_exact_phrases`: フレーズ検索
  - `test_conjunctive_search_returns_all_keywords_match`: AND検索
  - `test_title_boost_prioritizes_title_matches`: タイトルブースト

- **型定義の検証**:
  - `test_fts_search_result_contains_required_fields`: 必須フィールド
  - `test_fts_search_result_is_immutable`: 不変性

#### インフラストラクチャ層テスト（test_infrastructure.py）
- **FTS拡張の管理**:
  - `test_install_fts_extension_success`: 拡張のインストール
  - `test_initialize_fts_schema_with_extension_succeeds`: スキーマ初期化
  - `test_create_fts_index_success`: インデックス作成

- **エラーケース**:
  - `test_initialize_fts_schema_without_extension_returns_error`: 拡張なしでのエラー
  - `test_drop_nonexistent_fts_index_returns_error`: 存在しないインデックスの削除

### ⚠️ 不足している仕様化

1. **Numpyの使用**: BM25計算でnumpyを使用しているはずだが、明示的なテストがない
2. **パフォーマンス要件**: 検索時間の妥当性テストはあるが、具体的な閾値がない
3. **大規模データ**: 実用的なデータ量でのテストがない
4. **同時実行**: 並行アクセスのテストがない

## 3. テスト哲学との整合性評価

### 黄金律「リファクタリングの壁」の遵守
- ✅ **公開APIのみをテスト**: FTSService.index_documents(), .search()
- ✅ **実装詳細を避ける**: 内部のKuzuDBクエリ構造は隠蔽
- ✅ **振る舞いを検証**: 「何を入力すると何が返るか」に焦点

### レイヤー別テスト戦略
- ✅ **ドメイン層**: 純粋関数の単体テスト（BM25計算、ハイライト生成）
- ✅ **アプリケーション層**: 統合テストでユースケースを検証
- ✅ **インフラ層**: 実際のKuzuDB接続での統合テスト

### テスト＝仕様の確認
- ✅ **明確な担保内容**: 各テスト名が「何を保証するか」を表現
- ✅ **要件との対応**: FTS機能要件をカバー
- ✅ **ファイル命名規則**: `test_*.py` 形式を遵守

## 4. 結論

### 強み
1. **FTSの核心機能は十分に仕様化されている**
   - キーワード検索、BM25スコアリング、ハイライト
   - 大文字小文字区別なし、複数単語対応
   - エラーハンドリング

2. **テスト哲学に忠実**
   - 黄金律を遵守
   - 適切なレイヤー分離
   - 実行可能な仕様書として機能

### 改善点
1. **依存関係の明示的テスト**
   - numpyへの依存を明示するテスト追加
   - KuzuDB FTS拡張の機能境界テスト

2. **非機能要件のテスト**
   - パフォーマンステスト（具体的な閾値設定）
   - 大規模データでの動作確認
   - 同時実行時の振る舞い

3. **ドキュメント性の向上**
   - テストクラスにdocstring追加
   - 複雑なテストケースへのコメント

## 5. 推奨アクション
1. numpy使用を明示するテスト追加（例: BM25計算の数値精度テスト）
2. パフォーマンステストの閾値設定（例: 1000文書で検索1秒以内）
3. テストクラスへのdocstring追加で仕様の可読性向上