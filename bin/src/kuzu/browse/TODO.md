# Kuzu-Browse プロジェクト TODO リスト

## 概要

このTODOリストは、Kuzu-Browse プロジェクト（旧 wasm_deno）の残りのタスクをまとめたものです。プロジェクトは「ディレクトリ名変更フェーズ」が完了し、次の「リファクタリングフェーズ」および「エラーアプローチ統一フェーズ」を進める必要があります。

## 完了済み項目

- [x] wasm_deno -> browseへのディレクトリ名変更
- [x] deno.jsonのプロジェクト名更新
- [x] mod.tsの参照を動的取得に変更
- [x] CONVENTION.mdの参照パス更新
- [x] build.tsのコメントとログメッセージ更新

## リファクタリングフェーズ

### 1. インポート戦略の統一

- [x] `/home/nixos/bin/src/kuzu/browse/src/interface/App.tsx`
  - kuzu-wasmのインポートを修正（"@kuzu/kuzu-wasm@0.0.8" から "npm:kuzu-wasm@^0.8.0"に変更）
  - インポート方法をDenoの標準パターンに揃える
  
- [x] `/home/nixos/bin/src/kuzu/browse/src/main.ts`
  - 相対パスインポート（"../node_modules/kuzu-wasm"）を、Denoの標準的なインポート構文（"npm:kuzu-wasm"）に修正

### 2. API利用パターンの統一

- [ ] `/home/nixos/bin/src/kuzu/browse/src/interface/App.tsx`
  - Userテーブルのスキーマを`main.ts`と一致させる
  - APIの使用パターンを統一（`new kuzu.Database("")`パターンに統一）

### 3. ビルド・設定の整理

- [ ] `/home/nixos/bin/src/kuzu/browse/build.ts`
  - optimizeDepsの除外リストを確認し、インポート戦略と一致させる

- [ ] `/home/nixos/bin/src/kuzu/browse/index.html`
  - メタタグとViteサーバー設定の間でCOOP/COEPヘッダーの重複を確認し、一方に統一することを検討

## エラーアプローチ統一フェーズ

### 1. エラーハンドリングの統一

- [ ] `/home/nixos/bin/src/kuzu/browse/src/interface/App.tsx`
  - エラー処理を改善し、適切なクリーンアップを実装
  - エラーメッセージを標準化

- [ ] `/home/nixos/bin/src/kuzu/browse/src/main.ts`
  - エラー処理のパターンを確認し、App.tsxと一貫性を持たせる

### 2. 例外処理の追加

- [ ] `/home/nixos/bin/src/kuzu/browse/build.ts`
  - エラーハンドリングを追加し、サーバー起動失敗時の適切な対応を実装

- [ ] `/home/nixos/bin/src/kuzu/browse/mod.ts`
  - エラーハンドリングを追加し、モジュール実行時の例外に対処

## テスト・検証

- [ ] すべての変更後、アプリケーションが正常に動作することを確認
- [ ] `deno run -A build.ts` コマンドでサーバーが正常に起動することを確認
- [ ] ブラウザでCSVデータが正しく読み込まれ、表示されることを確認

## 将来的な改善点

- [ ] TypeScriptの型定義を充実させる
- [ ] ユニットテストの追加
- [ ] パフォーマンス最適化
- [ ] ドキュメントの充実化

## 注意事項

- WASM関連の設定は慎重に扱うこと
- クロスオリジン分離（COOP/COEP）の設定は、SharedArrayBufferの使用に必須
- 依存関係のバージョンは一貫性を持たせること

