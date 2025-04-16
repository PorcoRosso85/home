# schemeプロジェクト - 次のステップ

## 完了したタスク

### ソースコード構成の最適化
- ✅ ルートディレクトリ直下のTypeScriptファイル削除
- ✅ インターフェース層 (`src/interface`) への適切なファイル移動
  - ✅ `requirements-generator.ts` → `src/interface/requirements-generator.ts`
  - ✅ `generate-types-from-requirements.ts` → `src/interface/generate-types-from-requirements.ts`
- ✅ ユースケース層 (`src/usecase`) への適切なファイル移動
  - ✅ `requirements-to-function.ts` → `src/usecase/requirements-to-function.ts`
  - ✅ `requirements-deps.ts` → `src/usecase/requirements-deps.ts`
- ✅ デモ・サンプルファイルの移動
  - ✅ `demo.generate.ts` → `demo/demo.generate.ts`
  - ✅ `run_deps_test.ts` → `demo/run_deps_test.ts`
- ✅ 不要ファイルのアーカイブ
  - ✅ `generate-unified-types.ts` → `archive/generate-unified-types.ts`
- ✅ ファイル内の相対パス参照の更新
- ✅ README.mdの更新

### クリーンアップとエントリポイント統合
- ✅ CLIの統合 - `cli.ts`をメインエントリポイントとして実装
- ✅ nix shellを使用したshebangの適用
- ✅ `cli.ts`に実行権限の付与
- ✅ 統一要件管理と型生成コマンドの統合

### レイヤー構造の最適化
- ✅ usecase層は独立させずapplication層に統合
- ✅ 統合する際ファイル名に「xxxUsecase.ts」を付記

## 次のステップ

5. **外部コマンドの完全統合**
   - ✅ `requirements-generator.ts` のロジックを `cli.ts` に直接統合
   - ✅ `generate-types-from-requirements.ts` のロジックを `cli.ts` に直接統合
   - ✅ プロセス生成のオーバーヘッドを削減

6. **古いエントリポイントの廃止計画**
   - ✅ 移行期間を設けて開発者に通知
   - ✅ 非推奨エントリポイントとしてマークするコメントの追加
   - ✅ 古いファイルをアーカイブに移動するプランの策定

7. **出力ディレクトリパスの修正**
   - ✅ `RequirementsToFunctionCommand` の出力先ディレクトリを修正
   - ✅ `data/config` ディレクトリは使用しない設計に変更
   - ✅ 生成された関数定義JSONの出力先を `data/generated` に変更

8. **型生成プロセスの自動化**
   - ⬜ 型生成に必要なディレクトリの自動確認と作成
   - ⬜ 一連の型定義生成処理を行うシェルスクリプトの作成
   - ⬜ CI/CDパイプラインへの型生成フローの統合

## システム設計

### データフロー設計
- 統一要件ファイル (.require.json) は `data/requirements` ディレクトリに保存されます
- 生成された型スキーマファイル (.schema.json) は `data/generated` ディレクトリに出力されます
- `data/config` ディレクトリは今後使用しない設計に変更されます

### プロセスフロー
1. 統一要件JSON作成: `req-gen` コマンドで要件を定義し `data/requirements` に保存
2. 型生成: `generate-types` コマンドで要件ファイルから型スキーマを生成し `data/generated` に出力
3. 型の検証: `validate` コマンドで生成された型スキーマを検証

## 改善点

### ディレクトリ構造と自動化
1. **必要なディレクトリの自動生成**
   - 現状: 必要なディレクトリ (`data/config` など) が存在しない場合にエラーが発生
   - 改善案: コマンド実行時に必要なディレクトリを自動生成する機能を追加
   - 該当ファイル: `src/interface/cli.ts` の `executeRequirementsGeneratorCommand` メソッドを修正

2. **ディレクトリ確認関数の作成**
   - 現状: 各コマンドでディレクトリ確認を個別に実装または未実装
   - 改善案: 共通のディレクトリ確認・生成関数を作成し再利用
   - 実装案: `ensureDirectoryExists` ユーティリティ関数を作成

### エラーメッセージと例外処理
1. **詳細なエラーメッセージ**
   - 現状: エラーメッセージが具体的な対策を示していない
   - 改善案: エラー時に具体的な対策を含むメッセージを表示
   - 例: `configディレクトリが存在しません。'mkdir -p data/config'を実行してください。`

2. **自動リカバリーの実装**
   - 現状: エラー発生時にユーザーが手動で対応する必要がある
   - 改善案: 可能な場合は自動的に回復処理を実行するロジックの追加
   - 実装例: ディレクトリの自動生成や不足ファイルの自動生成

### パフォーマンス最適化
1. **外部コマンドの統合**
   - 現状: `req-gen` や `generate-types` は外部コマンドとして実行されている
   - 改善案: 外部コマンドを直接統合し、プロセス起動のオーバーヘッドを削減
   - アプローチ: `requirements-generator.ts` と `generate-types-from-requirements.ts` のロジックを直接インポート

2. **起動時初期化の最適化**
   - 現状: 全てのコマンドでメタスキーマリポジトリの初期化が必要
   - 改善案: 適切なレイジーロードメカニズムの実装
   - 実装案: コマンドがメタスキーマ情報を必要とする場合のみ初期化を実行

## 実装計画

### ディレクトリ構造の確認
1. READMEのディレクトリ構造説明を確認
2. 現実のディレクトリ構造と一致しているか検証
3. 不一致がある場合は修正
4. application層のcommand.tsの適切な配置を検討

### ドキュメント更新
1. 命名規則に関する説明をREADMEに追加
2. レイヤー構造の説明を更新
3. 使用例を最新化

### リリース計画
1. 移行手順書の作成
   - 古いディレクトリ構造からの移行手順
   - 新しいコード規約の説明
2. ユーザー向け通知の準備
