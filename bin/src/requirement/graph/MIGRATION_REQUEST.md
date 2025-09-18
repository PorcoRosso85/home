# VSS/FTSテスト移行要請

## 概要
requirement/graphモジュールは要件管理のビジネスロジックに責務を集中するため、VSS/FTS実装詳細のテストを各検索モジュールに移行することを要請します。

## 移行対象ファイル

### 1. test_search_adapter.py
- **現在地**: `/home/nixos/bin/src/requirement/graph/test_search_adapter.py`
- **内容**: SearchAdapter実装詳細の直接テスト（print文を使用した調査スクリプト）
- **移行先**: 削除推奨（正式なテストではなく調査用スクリプトのため）
- **代替案**: 必要な検証はvss_kuzu/fts_kuzu内で統合テストとして実装
- **理由**: print文を使用した手動実行スクリプトは規約違反

### 2. test_vss_issue.py
- **現在地**: `/home/nixos/bin/src/requirement/graph/test_vss_issue.py`
- **内容**: VSS類似度計算の問題調査スクリプト
- **移行先**: `vss_kuzu/tests/test_similarity_calculation.py`として再実装
- **検証内容**: 
  - 類似度スコアが0.0にならないこと
  - 日本語テキストでの類似検索が正常動作すること
- **理由**: VSS実装の動作検証はvss_kuzuの責務

### 3. test_vss_with_connection.py
- **現在地**: `/home/nixos/bin/src/requirement/graph/test_vss_with_connection.py`
- **内容**: VSS接続処理の検証
- **移行先**: `vss_kuzu/tests/test_connection_handling.py`として再実装
- **検証内容**:
  - 永続的データベースでの接続管理
  - 複数接続の同時利用
- **理由**: VSSの接続管理はvss_kuzuの責務

### 4. test_duplicate_simple.py
- **現在地**: `/home/nixos/bin/src/requirement/graph/test_duplicate_simple.py`
- **内容**: 重複検出の簡易テスト
- **判断**: 内容確認後、ビジネスロジックならe2e/internal/へ移動、実装詳細なら削除

## 移行後の責務分担

### vss_kuzu/fts_kuzuで保証すべきこと
1. **プロトコル準拠**: VSSAlgebra/FTSAlgebraの完全実装
2. **エラーハンドリング**: 
   - VECTOR拡張が無い場合の明確なエラー
   - 不正パラメータの適切な拒否
   - リソース不足時の graceful degradation
3. **性能特性**: インデックス作成と検索の時間計測
4. **日本語対応**: 日本語テキストでの正常動作

### requirement/graphに残るテスト
1. **e2e/internal/**: ビジネス価値の検証
   - 重複検出機能の動作
   - 要件管理ワークフロー
2. **domain/**: ドメインロジックの単体テスト
   - 循環依存検出
   - 制約検証
3. **application/**: 統合ポイントのテスト（新規作成推奨）
   - SearchAdapterとリポジトリの連携
   - ビジネスルールの適用

## 移行によるメリット
1. **責務の明確化**: 各モジュールが自身の品質に責任を持つ
2. **並列開発**: VSS/FTS/RGLの独立した開発が可能
3. **テスト速度**: 必要なテストのみ実行可能
4. **保守性向上**: 変更の影響範囲が明確

## アクション要請
1. 上記ファイルの内容を確認し、各モジュールでの再実装を検討してください
2. 正式なテストとして、規約に準拠した形で実装してください（print文禁止）
3. 移行完了後、requirement/graphから該当ファイルを削除します

以上