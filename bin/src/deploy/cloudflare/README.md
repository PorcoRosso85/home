# Cloudflare Deploy

Cloudflareへのデプロイメントを管理するディレクトリ。

## 責務

- Cloudflareへのアプリケーションデプロイ設定
- Cloudflare Workers/Pages向けのビルド・デプロイプロセス管理
- Cloudflare固有の設定ファイル管理
- デプロイメントパイプラインの実装

## ディレクトリ構成

```
cloudflare/
├── README.md           # このファイル
├── workers/           # Cloudflare Workers関連
├── pages/            # Cloudflare Pages関連
└── scripts/          # デプロイスクリプト
```

## 使用方法

### Workers デプロイ

```bash
# TODO: デプロイコマンドを追加
```

### Pages デプロイ

```bash
# TODO: デプロイコマンドを追加
```

## 設定

### 環境変数

- `CLOUDFLARE_API_TOKEN`: Cloudflare APIトークン
- `CLOUDFLARE_ACCOUNT_ID`: アカウントID

## 関連ドキュメント

- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [Cloudflare Pages Documentation](https://developers.cloudflare.com/pages/)