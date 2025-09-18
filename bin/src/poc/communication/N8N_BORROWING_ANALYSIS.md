# n8n借用分析

## 概要
本POCでは、n8nのOAuth2およびGmail実装を参考にしていますが、**完全な借用ではなく、概念の参考と一部実装パターンの借用**です。

## 借用レベルの分類

### 1. 直接借用（コードをほぼそのまま移植）
- **Gmail API URLとスコープ**
  - `oauth_config.ts`: Gmail認証URL、トークンURL、スコープ定義
  - 借用元: `packages/nodes-base/credentials/GoogleOAuth2Api.credentials.ts`
  - 理由: Google APIの公式仕様のため変更不要

### 2. 概念借用（アーキテクチャや処理フローを参考）
- **OAuth2フロー全体**
  - `oauth_helper.ts`: 認証URL生成、トークン交換、リフレッシュ
  - 参考元: `packages/cli/src/controllers/oauth/oauth2-credential.controller.ts`
  - 変更点: サーバーサイド実装をCLI用に変換、Deno向けに書き直し

- **Gmail APIクエリ構築**
  - `gmail_client.ts`: クエリパラメータ構築ロジック
  - 参考元: `packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts`の`prepareQuery`
  - 変更点: TypeScript型定義を追加、Deno標準APIを使用

### 3. 独自実装（n8nと異なるアプローチ）
- **プロバイダー統一管理**
  - `oauth_config.ts`: 全プロバイダーを1つのオブジェクトで管理
  - n8nの方式: 各プロバイダーごとに個別のcredentialファイル
  - 理由: CLIでの使いやすさを優先

- **認証情報の管理**
  - CLI実装: 環境変数またはCLI引数
  - n8nの方式: データベースに暗号化保存
  - 理由: CLIツールとしてのシンプルさ

- **トークン保存**
  - CLI実装: ローカルJSONファイル（プロバイダー別）
  - n8nの方式: データベース内で暗号化管理
  - 理由: POC段階でのシンプルな実装

## 主要な変更点

### 1. 実行環境の違い
- n8n: Node.js + Express サーバー
- POC: Deno CLI アプリケーション

### 2. 認証フローの違い
- n8n: Webサーバーでコールバック受信
- POC: 手動でコードをコピー＆ペースト

### 3. エラーハンドリング
- n8n: 複雑なエラーハンドリングとリトライ機構
- POC: シンプルなtry-catchとエラーメッセージ

## 借用の正当性
1. **OAuth2仕様**: 標準プロトコルのため実装パターンは限定的
2. **Google API仕様**: 公式ドキュメントに基づく共通実装
3. **実装の変換**: Node.js→Denoへの移植で大幅な書き換え

## まとめ
- 約30%: 直接借用（API URL、スコープなど仕様に基づく部分）
- 約40%: 概念借用（処理フローやアーキテクチャパターン）
- 約30%: 独自実装（CLI向けの最適化、Deno対応）

n8nの実装は**参考資料**として活用し、CLIツールに適した形で再実装しています。