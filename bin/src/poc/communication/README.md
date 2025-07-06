# Communication POC

CLIで外界とのコミュニケーションを操作するためのPOC

## 目的
- 外部サービスとのインタラクションをCLI経由で制御
- 初回認証後は完全自動化

## 構成
```
communication/
├── mail/                      # メール機能実装
│   ├── core.ts               # ドメインモデル
│   ├── application/          # アプリケーション層
│   │   └── mail_service.ts   # メールサービス
│   ├── infrastructure/       # インフラ層
│   │   ├── gmail_official_client.ts  # Google公式ライブラリ使用
│   │   ├── auto_auth_manager.ts      # 自動認証マネージャー
│   │   └── oauth_config.ts           # OAuth2プロバイダー設定
│   └── cli_full_auto.ts     # 完全自動認証CLI
└── source/
    └── n8n/                  # n8n本体（参考実装）
```

## Gmail CLI

### 特徴
- 初回認証時はブラウザが自動で開く
- 認証コードも自動取得（手動コピー不要）
- 2回目以降は完全自動（トークン自動更新）
- Google公式ライブラリ使用（Apache 2.0ライセンス）

### 使用方法

```bash
# 初回セットアップ
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"

# 実行方法

# 1. nix runコマンド（推奨）
nix run .#run          # Gmail CLIを実行
nix run .#run -- --unread  # 未読メールのみ表示

# 2. 直接実行
./gmail
./gmail --unread
```

### 詳細設定
詳細は [SIMPLE_AUTH_SETUP.md](./SIMPLE_AUTH_SETUP.md) を参照

## 利用可能なコマンド

```bash
nix run .         # このREADMEを表示（デフォルト）
nix run .#run     # Gmail CLIを実行
nix run .#test    # テストを実行
```

## テスト実行

```bash
nix run .#test
```