# R2 CORS Setup Guide

## 問題

wrangler 4.30.0では`wrangler r2 bucket cors set`コマンドに既知の問題があり、JSONフォーマットがAPIと一致しません。

参考: https://github.com/cloudflare/workers-sdk/issues/8486

## 解決方法

### 方法1: Cloudflare Dashboard から設定（推奨）

1. Cloudflare Dashboard にログイン
2. R2 > Buckets > `waku-wasm` を選択
3. Settings タブを開く
4. CORS Policy セクションで「Add CORS policy」をクリック
5. JSONタブで以下を入力：

```json
[
  {
    "AllowedOrigins": ["http://localhost:8787", "http://localhost:8788", "https://example.com"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["Content-Type", "Range", "If-Match", "If-None-Match"],
    "ExposeHeaders": ["Content-Length", "Content-Type", "ETag", "Content-Range"],
    "MaxAgeSeconds": 86400
  }
]
```

**注意**: 
- `AllowedMethods`に`OPTIONS`を含めるとエラーになる場合があります
- `AllowedOrigins`に実際に使用するオリジンを追加してください
- ワイルドカード`"*"`は動作しない場合があります

### 方法2: API直接呼び出し

```bash
# APIトークンが必要
export CF_API_TOKEN="your-api-token"
export ACCOUNT_ID="3d17cd263c27a0ea241f0a8fc09ac2bb"

curl -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/r2/buckets/waku-wasm/cors" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @cors-api.json
```

### 方法3: Custom Domain経由でのアクセス

R2バケットにCustom Domainを設定すると、CORSポリシーなしでもアクセス可能：

1. R2 > Buckets > `waku-wasm` > Settings > Custom Domains
2. ドメインを追加（例: `wasm.your-domain.com`）
3. DNSレコードが自動作成される
4. HTTPSでアクセス可能に

## 確認方法

```bash
# ブラウザのDevToolsで確認
fetch('https://wasm.your-domain.com/test.wasm')
  .then(res => res.headers.get('Access-Control-Allow-Origin'))
```

## 注意事項

- wrangler の将来のバージョンで修正される予定
- Custom Domain設定が最も簡単で確実
- APIトークンを使う場合は、R2権限が必要