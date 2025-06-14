# Kuzu-Browse プロジェクト TODO リスト

## 概要

このTODOリストは、Kuzu-Browse プロジェクト（旧 wasm_deno）の残りのタスクをまとめたものです。プロジェクトは「ディレクトリ名変更フェーズ」が完了し、次の「リファクタリングフェーズ」および「エラーアプローチ統一フェーズ」を進める必要があります。

## 完了済み項目

- [x] wasm_deno -> browseへのディレクトリ名変更
- [x] deno.jsonのプロジェクト名更新
- [x] mod.tsの参照を動的取得に変更
- [x] CONVENTION.mdの参照パス更新
- [x] build.tsのコメントとログメッセージ更新

## v0.1.1 リファクタリングフェーズ（追加）

### アーキテクチャ整理タスク

- [ ] **インターフェースレイヤー構造変更**
  - [ ] `src/interface/Layout.tsx` 作成（App.tsxからレイアウト分離）
  - [ ] `src/interface/Page.tsx` 作成（VersionTreeView.tsxから名称変更）
  - [ ] `src/interface/presentation/` ディレクトリ作成
  - [ ] `src/interface/elements/` ディレクトリ作成
  
- [ ] **ファイル移動・名前変更**
  - [ ] `VersionStates.tsx` → `presentation/VersionStates.tsx`
  - [ ] `LocationUris.tsx` → `presentation/LocationUris.tsx`  
  - [ ] `TreeView.tsx` → `components/Tree.tsx`
  - [ ] `TreeNode.tsx` → `components/Node.tsx`
  - [ ] `ErrorView.tsx` → `elements/ErrorView.tsx`
  - [ ] `LoadingView.tsx` → `elements/LoadingView.tsx`
  - [ ] `NodeDetailsPanel.tsx` → `elements/NodeDetailsPanel.tsx`

- [ ] **import文の修正**
  - [ ] 全ファイルのimportパスを新構造に対応
  - [ ] TypeScriptエラーの解消

### **削除用DMLとUI表示（重要）**

- [ ] **削除用DMLクエリの実装**
  ```cypher
  // mv前のファイルを削除するクエリが必要
  // 現在のDMLはmv前ファイル（例：VersionTreeView.tsx）を認識できていない
  MATCH (l:LocationURI {id: "file:///path/to/old/file.tsx"})
  DETACH DELETE l
  ```

- [ ] **削除されたファイルのUI表示改善**
  - [ ] 削除されたLocationURIを区別して表示
  - [ ] 「削除されました」等の明確な表示
  - [ ] バージョン間での削除ファイル追跡機能

- [ ] **DML改善課題**
  - [ ] `version_batch_operations.cypher` の削除対応
  - [ ] 移動前ファイルの自動削除ロジック
  - [ ] バージョン間差分での削除ファイル検出

## リファクタリングフェーズ

### 1. インポート戦略の統一

- [x] `/home/nixos/bin/src/kuzu/browse/src/interface/App.tsx`
  - kuzu-wasmのインポートを修正（"@kuzu/kuzu-wasm@0.0.8" から "npm:kuzu-wasm@^0.8.0"に変更）
  - インポート方法をDenoの標準パターンに揃える
  
- [x] `/home/nixos/bin/src/kuzu/browse/src/main.ts`
  - 相対パスインポート（"../node_modules/kuzu-wasm"）を、Denoの標準的なインポート構文（"npm:kuzu-wasm"）に修正

### 2. API利用パターンの統一

- [x] `/home/nixos/bin/src/kuzu/browse/src/interface/App.tsx`
  - Userテーブルのスキーマを`main.ts`と一致させる
  - APIの使用パターンを統一（`new kuzu.Database("")`パターンに統一）

### 3. ビルド・設定の整理

- [x] `/home/nixos/bin/src/kuzu/browse/build.ts`
  - optimizeDepsの除外リストを確認し、インポート戦略と一致させる

- [x] `/home/nixos/bin/src/kuzu/browse/index.html`
  - メタタグとViteサーバー設定の間でCOOP/COEPヘッダーの重複を確認し、一方に統一することを検討

## エラーアプローチ統一フェーズ

### 1. エラーハンドリングの統一

- [x] `/home/nixos/bin/src/kuzu/browse/src/interface/App.tsx`
  - エラー処理を改善し、適切なクリーンアップを実装
  - エラーメッセージを標準化

- [x] `/home/nixos/bin/src/kuzu/browse/src/main.ts`
  - エラー処理のパターンを確認し、App.tsxと一貫性を持たせる

### 2. 例外処理の追加

- [x] `/home/nixos/bin/src/kuzu/browse/build.ts`
  - エラーハンドリングを追加し、サーバー起動失敗時の適切な対応を実装

- [ ] `/home/nixos/bin/src/kuzu/browse/mod.ts`
  - エラーハンドリングを追加し、モジュール実行時の例外に対処

## テスト・検証

- [ ] すべての変更後、アプリケーションが正常に動作することを確認
- [ ] `deno run -A build.ts` コマンドでサーバーが正常に起動することを確認
- [ ] ブラウザでCSVデータが正しく読み込まれ、表示されることを確認
- [ ] **v0.1.1リファクタリング後の動作確認**

## 将来的な改善点

- [ ] TypeScriptの型定義を充実させる
- [ ] ユニットテストの追加
- [ ] パフォーマンス最適化
- [ ] ドキュメントの充実化
- [ ] **削除ファイル管理の自動化**

## 注意事項

- WASM関連の設定は慎重に扱うこと
- クロスオリジン分離（COOP/COEP）の設定は、SharedArrayBufferの使用に必須
- 依存関係のバージョンは一貫性を持たせること
- **DMLでの削除処理は慎重に実装すること（データ整合性重要）**

