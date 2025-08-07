# Email Archive POC

## 概要

Cloudflare Email Routing機能を使用して、Worker経由でローカルS3互換ストレージ（MinIO）へ全メールをアーカイブする実装のPOC。

## 目的

- 受信したすべてのメールを自動的にローカルS3に保存
- メールの長期保存とバックアップ
- 後からの検索・分析を可能にする
- データの完全なローカル管理

## アーキテクチャ

```
┌─────────────┐    ┌──────────────────┐    ┌─────────┐    ┌──────────┐
│  外部送信者  │───>│ Cloudflare Email │───>│ Worker  │───>│  MinIO   │
└─────────────┘    │    Routing       │    └─────────┘    │  (S3)    │
                   └──────────────────┘                    └──────────┘
                            │                                   ↑
                            ▼                                   │
                   ┌──────────────────┐                        │
                   │  通常の受信箱    │                        │
                   └──────────────────┘                        │
                                                              Local
```

## 実装要素

### 1. Email Routing設定
- カスタムドメインのメール受信設定
- Worker へのルーティングルール

### 2. Email Worker
- メール受信イベントのハンドリング
- メールデータの構造化
- MinIO S3 APIへの保存処理
- エラーハンドリングとリトライ

### 3. MinIO（ローカルS3）
- メールデータの永続化
- 階層的な保存構造（年/月/日/メールID）
- メタデータの管理
- ローカルでのS3互換API提供

## データ構造

### S3オブジェクトキー
```
emails/
├── 2024/
│   └── 01/
│       └── 15/
│           ├── {message-id}.eml     # 生のメールデータ
│           └── {message-id}.json    # メタデータ
```

### メタデータ構造
```json
{
  "messageId": "unique-message-id",
  "receivedAt": "2024-01-15T10:30:00Z",
  "from": "sender@example.com",
  "to": ["recipient@yourdomain.com"],
  "subject": "メールの件名",
  "size": 12345,
  "attachments": [
    {
      "filename": "document.pdf",
      "contentType": "application/pdf",
      "size": 54321
    }
  ],
  "headers": {
    "X-Original-Header": "value"
  }
}
```

## セキュリティ考慮事項

1. **アクセス制御**
   - MinIOバケットは非公開設定
   - Worker のみがアクセス可能
   - IAMポリシーによる細かいアクセス制御

2. **データプライバシー**
   - 個人情報を含むメールの適切な管理
   - 保存期間ポリシーの設定
   - ローカル管理によるデータ主権の確保

3. **暗号化**
   - MinIOでの保存時暗号化（SSE-S3）
   - 転送時のTLS使用
   - Worker-MinIO間の通信暗号化

## 実装ステップ

1. MinIOサーバーのセットアップとバケット作成
2. Cloudflare アカウントでEmail Routingを有効化
3. Email Worker の実装（S3 SDK使用）
4. Worker環境変数の設定（MinIOエンドポイント、認証情報）
5. Worker と MinIO の連携設定
6. テストメールでの動作確認

## 制限事項

- Email Routing の最大メールサイズ: 25MB
- Worker の実行時間制限: 30秒（有料プランで延長可能）
- MinIOのストレージ容量はローカルディスク依存
- Worker-MinIO間のネットワーク遅延考慮

## 今後の拡張案

- メール検索API の実装
- 添付ファイルの個別管理
- メール分析機能の追加
- 自動削除ポリシーの実装
- バックアップとレプリケーション機能

## 実装詳細

### Worker実装の要点

```javascript
// Email Workerの基本構造
export default {
  async email(message, env, ctx) {
    // 1. メールデータの取得
    const rawEmail = await message.raw();
    
    // 2. メタデータの抽出
    const metadata = {
      messageId: message.headers.get("message-id"),
      from: message.from,
      to: message.to,
      subject: message.headers.get("subject"),
      receivedAt: new Date().toISOString()
    };
    
    // 3. S3への保存
    const s3Client = new S3Client({
      endpoint: env.MINIO_ENDPOINT,
      credentials: {
        accessKeyId: env.MINIO_ACCESS_KEY,
        secretAccessKey: env.MINIO_SECRET_KEY
      }
    });
    
    // 4. オブジェクトキーの生成
    const date = new Date();
    const key = `emails/${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}/${metadata.messageId}`;
    
    // 5. 保存処理
    await Promise.all([
      // 生メールの保存
      s3Client.putObject({
        Bucket: env.BUCKET_NAME,
        Key: `${key}.eml`,
        Body: rawEmail,
        ContentType: 'message/rfc822'
      }),
      // メタデータの保存
      s3Client.putObject({
        Bucket: env.BUCKET_NAME,
        Key: `${key}.json`,
        Body: JSON.stringify(metadata),
        ContentType: 'application/json'
      })
    ]);
  }
};
```

### MinIO設定

```yaml
# docker-compose.yml
version: '3.8'
services:
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: miniopassword
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  minio_data:
```

### バケットポリシー設定

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": ["arn:aws:iam::*:user/email-worker"]
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::email-archive/*"
    }
  ]
}
```

## 単一責務の原則

このシステムは「メールのアーカイブ」という単一の責務のみを持つ：

1. **受信したメールの保存のみ**
   - メール転送、フィルタリング、変換は行わない
   - 純粋にアーカイブ機能のみ提供

2. **データの不変性**
   - 一度保存したメールは変更しない
   - 削除はポリシーに基づく自動削除のみ

3. **他システムとの独立性**
   - メール配信システムから独立
   - 検索・分析システムから独立
   - アーカイブAPIのみを提供