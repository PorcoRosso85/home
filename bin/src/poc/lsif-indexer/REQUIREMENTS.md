# NixdAdapter LSIF-Core統合 要件定義書

## プロジェクト概要
**目的**: 既存のNixdAdapterにlsif-core統合機能を追加し、Nixファイルのシンボル情報をLSIFグラフ形式で処理可能にする

**背景**: 
- 現在のNixdAdapterはLSP経由でDocumentSymbolを取得可能
- lsif-coreはCodeGraph/Symbol形式でのグラフ構築をサポート
- TypeScript/Go等の他言語アダプターでは既にDocumentSymbol→lsif_core::Symbol変換が実装済み

## 要件定義

### 機能要件 (What)
1. **DocumentSymbol→lsif_core::Graph変換機能**
   - NixdAdapter::to_lsif_graph()メソッド追加
   - Vec<DocumentSymbol> → lsif_core::CodeGraph変換
   - 階層構造の適切な変換（親子関係の保持）

2. **Nixシンボル種別の適切なマッピング**
   - Nix特有のシンボル（inputs、outputs、let bindings等）の分類
   - lsif_core::SymbolKindへの適切な変換

3. **テストケース実装**
   - test_nix_to_lsif_conversion()関数追加
   - flake.nix、default.nix等のテストデータ
   - 変換結果の正確性検証

### 非機能要件 (Why)
- **統合性**: 他言語アダプター（TypeScript/Go/Python）との一貫性確保
- **拡張性**: 将来的なNixシンボル種別拡張への対応
- **性能**: 大規模Nixプロジェクトでの変換処理効率
- **保守性**: 既存コードとの整合性維持

### 制約条件
- 既存のNixdAdapterインターフェース（LanguageAdapter、LspAdapter）を変更しない
- unified_indexer.rsの実装パターンを踏襲
- LSP経由でのDocumentSymbol取得は既存実装を流用

## 想定される利用場面
1. **Nixプロジェクトの静的解析**: flake.nixの依存関係分析
2. **シンボル検索の高速化**: lsif-coreのインデックス機能活用
3. **AI支援開発**: LLMによるNixコード理解の向上
4. **IDE統合**: 高速なシンボル参照・定義ジャンプ

## 成功基準
- [ ] to_lsif_graph()メソッドが実装され、DocumentSymbolからCodeGraphへの変換が動作
- [ ] Nixシンボル種別がlsif_core::SymbolKindに適切にマッピング
- [ ] 単体テストがPASSし、変換精度が95%以上
- [ ] 既存機能（LSP統合等）に回帰なし
- [ ] 他言語アダプターとの一貫したAPI設計

## 参考実装
- `/crates/lsp/src/unified_indexer.rs`: DocumentSymbol変換の実装例
- `/crates/lsp/src/adapter/typescript.rs`: 言語固有アダプターの構造
- `/crates/lsp/src/adapter/go.rs`: build_reference_pattern実装例

## 対象ファイル
- **メイン実装**: `/crates/lsp/src/adapter/nixd.rs`
- **テスト追加**: `/crates/lsp/src/adapter/nixd.rs` (tests module)
- **型定義参照**: `/crates/core/src/lib.rs` (lsif_core types)