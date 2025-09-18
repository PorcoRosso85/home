# 移行時のテストカバレッジ分析

## 現在カバーされているテスト項目

### SearchAdapter関連
1. **初期化処理**
   - VSS/FTSモジュールの可用性チェック ✓
   - 共有コネクションでの初期化 ✓
   - エラー時の処理 ✓

2. **インデックス追加（add_to_index）**
   - 正常系：要件の追加 ✓
   - VSS/FTS両方へのインデックス ✓

3. **類似検索（search_similar）**
   - 日本語テキストでの検索 ✓
   - 結果のランキング ✓
   - スコア計算 ✓

4. **重複チェック（check_duplicates）**
   - 閾値による判定 ✓
   - 結果フォーマット ✓

5. **ハイブリッド検索（search_hybrid）**
   - VSS+FTSの組み合わせ ✓

### VSS固有機能
1. **類似度計算**
   - 0.0にならないことの確認 ✓
   - 完全一致時の高スコア ✓
   - 意味的類似性 ✓

2. **永続化**
   - 永続DBでの動作 ✓
   - インメモリDBでの動作 ✓

### 統合動作
1. **テンプレート経由の重複検出**
   - create_requirementでの警告 ✓
   - 警告内容の正確性 ✓

## 移行によるリスク

### 低リスク（既存E2Eでカバー）
- 重複検出のビジネスロジック
- テンプレート経由の動作
- ユーザー視点の機能

### 中リスク（移行先で再実装必要）
- SearchAdapterの各メソッドの詳細動作
- エラーハンドリングの網羅性
- 日本語テキストの処理

### 高リスク（明示的な移行が必要）
1. **search_hybrid**の詳細実装
   - VSS/FTSの結果マージロジック
   - スコアの正規化

2. **エッジケース**
   - 空のインデックスでの検索
   - 大量データでの性能
   - 同時アクセス

## 移行時の必須確認事項

### requirement/graph側
1. E2Eテストがすべてパスすること
2. template_processorとの統合が維持されること

### vss_kuzu側で必須
1. add_to_indexに相当する機能テスト
2. search_similarの全機能テスト
3. 日本語テキストのテスト

### fts_kuzu側で必須
1. add_to_indexに相当する機能テスト
2. キーワード検索の精度テスト
3. 特殊文字のエスケープ

## デグレ防止策

1. **移行前**
   ```bash
   # 現在の全テスト結果を記録
   cd /home/nixos/bin/src/requirement/graph
   nix run .#test -- --json-report --json-report-file=before_migration.json
   ```

2. **移行後**
   ```bash
   # 移行後の全テスト結果を記録
   nix run .#test -- --json-report --json-report-file=after_migration.json
   
   # VSS/FTSでの新規テスト実行
   cd /home/nixos/bin/src/search/vss_kuzu
   nix run .#test
   
   cd /home/nixos/bin/src/search/fts_kuzu
   nix run .#test
   ```

3. **確認項目**
   - [ ] requirement/graphのE2Eテストが全パス
   - [ ] VSS/FTSの新規テストが全パス
   - [ ] 統合時の動作確認

## 結論

移行によるデグレリスクは存在するが、以下により最小化可能：

1. E2Eテストによるビジネスロジックの保護
2. 移行先での明示的なテスト実装
3. 移行前後のテスト結果比較

最もリスクが高いのは`search_hybrid`機能だが、これはE2Eテストでカバーされているため、実装詳細が変わってもビジネス価値は保証される。