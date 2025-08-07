# Email Send Service

## 責務

このサービスは以下の責務を持つ:

1. **ストレージアダプターの受け取り**
   - 下書きメールを保存・取得するためのストレージアダプターをDIで受け取る

2. **下書きメールの認識**
   - ストレージアダプターを通じて下書きメールのデータを取得
   - 送信対象のメールを識別

3. **メール送信**
   - 送信アダプターを使用して実際のメール送信処理を実行

## 初期装備

### AWS SES (Simple Email Service)

初期の送信アダプターとしてAWS SESを使用する。

#### 必要な設定

1. **AWS認証情報**
   - AWS Access Key ID
   - AWS Secret Access Key
   - リージョン設定（例: `us-east-1`, `ap-northeast-1`）

2. **SES設定**
   - 送信元メールアドレスの検証
   - 送信制限の確認（サンドボックスモード）
   - 本番環境への移行申請（必要に応じて）

#### 実装構成

```
send/
├── flake.nix              # Nix環境定義
├── package.json           # Bunプロジェクト設定
├── tsconfig.json          # TypeScript設定
├── bun.lockb              # Bunロックファイル
├── src/
│   ├── domain/
│   │   ├── email.ts       # メールエンティティ
│   │   └── ports.ts       # アダプターインターフェース
│   ├── adapters/
│   │   ├── storage/       # ストレージアダプター実装
│   │   └── sender/
│   │       └── ses.ts     # AWS SES送信アダプター
│   ├── application/
│   │   └── send-service.ts # メール送信サービス
│   └── index.ts           # エントリポイント
└── tests/                 # テストコード
```

## アーキテクチャ

ヘキサゴナルアーキテクチャを採用し、ビジネスロジックを外部依存から分離する:

- **Domain層**: メールエンティティと送信ルール
- **Ports**: ストレージと送信のインターフェース定義
- **Adapters**: AWS SESなどの具体的な実装
- **Application層**: ユースケースの実装

## 依存関係

- Bun 1.0+
- TypeScript 5.0+
- @aws-sdk/client-ses (AWS SDK v3 for SES)
- 下書きストレージサービス（../draft）

## 開発環境

```bash
# Nix開発環境の起動
nix develop

# 依存関係のインストール
bun install

# 開発サーバーの起動
bun run dev

# テストの実行
bun test

# ビルド
bun build
```