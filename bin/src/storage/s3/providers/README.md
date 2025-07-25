# S3 Storage Providers

## 目的

S3互換ストレージサービスの具体的な実装を提供するプロバイダーディレクトリです。
各プロバイダーは共通のインターフェースを実装し、アプリケーションから透過的に利用できます。

## 各プロバイダーの責務

- **接続管理**: 各サービス固有の認証・接続設定
- **API実装**: S3互換APIの具体的な実装
- **エラーハンドリング**: サービス固有のエラー処理
- **最適化**: 各サービスの特性に応じたパフォーマンス最適化

## 追加予定のプロバイダー

- **aws**: Amazon S3の公式実装
- **in-memory**: テスト用のインメモリ実装
- **minio**: MinIOサーバー向け実装

## Cloudflare R2プロバイダー

### 特徴
- **低コスト**: Amazon S3と比較して大幅に安価な料金体系
- **エグレス料金無料**: データ転送（ダウンロード）に対する課金なし
- **S3互換API**: 既存のS3クライアント/SDKをそのまま利用可能

### 実装詳細
R2プロバイダーはS3互換性を最大限活用した実装となります：

```typescript
// 必要な設定項目
interface R2Config {
  accountId: string;      // CloudflareアカウントID
  accessKeyId: string;    // R2 APIトークン
  secretAccessKey: string;// R2 APIシークレット
  bucketName: string;     // バケット名
  endpoint?: string;      // カスタムエンドポイント（オプション）
}
```

### 利点
- グローバルなエッジネットワークによる低レイテンシ
- 自動レプリケーションによる高可用性
- Cloudflare Workersとの統合による柔軟な処理

## Future Features

### POCとの機能差分
POCディレクトリ（`/home/nixos/bin/src/poc/`）で実証済みの機能のうち、本番実装に未統合のものがあります。これらは段階的に実装予定です。

### 将来実装予定の機能

#### 1. CLI統合機能
- **MinIO Client (mc) 統合**: mcコマンドを使用したR2バケット操作
- **Wrangler統合**: wrangler.tomlからの設定読み込みとコマンド実行
- **クロスCLIブリッジ**: mc/wrangler間の相互運用性

#### 2. 環境管理機能
- **.env.local自動読み込み**: プロジェクトルートの環境変数ファイル自動検出
- **環境変数テンプレート生成**: .env.exampleの自動生成と型安全な定義
- **MC_HOST_r2エイリアス設定**: MinIO Client互換の環境変数自動設定
- **環境設定検証**: 必須変数の存在確認と接続テスト
- **複数環境プロファイル管理**: dev/staging/prod環境の切り替え

### テストファイル参照
将来実装予定機能の詳細な仕様とskipテストは以下のファイルで確認できます：
- [`providers/r2-future-features.test.ts`](./r2-future-features.test.ts)

各skipテストには以下の情報が含まれています：
- Skip理由と未実装の機能説明
- 実装時の期待動作
- POCディレクトリへの参照
- 実装ガイドライン