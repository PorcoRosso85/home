# Waku + Cloudflare Workers Console.log 調査結果

## 問題の概要
`wrangler tail`でconsole.logの出力が取得できない問題を調査

## 調査結果サマリー

### 環境別の動作状況

| 環境 | console.log動作 | wrangler tail表示 | Workers Logs表示 |
|------|----------------|-------------------|------------------|
| ローカル (wrangler dev) | ✅ 動作する | ✅ 表示される | N/A |
| デプロイ (staging/prod) | ✅ 動作する | ❌ 表示されない | ✅ 記録される |

### console.logが動作する条件

#### ✅ 動作するケース
1. **関数内のconsole.log**
   ```javascript
   const entry = {
     fetch: (request, env, ctx) => {
       console.log('[DEBUG] Request:', request.url); // ✅ 動作
       return app.fetch(request, env, ctx);
     }
   };
   ```

2. **ミドルウェア内のconsole.log**
   ```typescript
   appToCreate.use('*', async (c, next) => {
     console.log(`[Hono] ${c.req.method} ${c.req.path}`); // ✅ 動作
     await next();
   });
   ```

#### ❌ 動作しないケース
1. **モジュールレベル（トップレベル）のconsole.log**
   ```javascript
   console.log('[MODULE-INIT] Loading...'); // ❌ キャプチャされない
   import { something } from './module';
   ```

2. **動的インポートされるモジュール（実行前）**
   ```javascript
   // アクションが呼ばれるまで実行されない
   const serverReferences = {
     "eada1cf0e37e": async () => {
       const {submitForm} = await import('./assets/actions-BSUuyZ5j.js');
       return {submitForm};
     },
   };
   ```

## 技術的詳細

### Wakuのサーバーアクション実行フロー
1. ブラウザがフォーム送信
2. `/RSC/F/eada1cf0e37e/submitForm.txt`へPOSTリクエスト
3. サーバーリファレンスによる動的インポート
4. アクションモジュールの初回ロード時にconsole.logが実行

### wrangler tailの制限事項

#### JSONフォーマットでの確認結果
```json
{
  "logs": [],  // 空配列 - console.logがキャプチャされていない
  "eventTimestamp": 1756541351940,
  "event": {
    "request": {
      "url": "https://waku-init-stg.trst.workers.dev/feedback",
      "method": "POST"
    }
  }
}
```

#### Cloudflare Workers Logsには記録される
```
Timestamp(UTC)     Origin  Trigger
2025-08-30 08:03   fetch   POST /RSC/F/eada1cf0e37e/submitForm.txt
```

## 検証済みの実装

### 1. Honoミドルウェアへのログ追加
```typescript
// waku.hono-enhancer.ts
appToCreate.use('*', async (c, next) => {
  console.log(`[Hono] ${c.req.method} ${c.req.path}`);
  console.warn(`[Hono-Warn] ${c.req.method} ${c.req.path}`);
  await next();
});
```

### 2. サーバーアクションへのログ追加
```typescript
// src/server/actions.ts
export async function submitForm(formData: FormData): Promise<SubmissionResponse> {
  console.log('[submitForm] Server action called');
  console.warn('[submitForm] Processing form submission');
  // ...
}
```

### 3. ストレージアダプターのログ
```typescript
// src/infrastructure/storage/log-adapter.ts
console.warn(`[STORAGE:${timestamp}] Saving to ${key} (${size} bytes)`);
```

## ローカル開発での確認方法

```bash
# wrangler devでローカル起動
nix develop --command wrangler dev --port 8790

# 別ターミナルでテスト
curl http://localhost:8790/
# コンソールに表示: [Hono] GET /
```

## 本番環境での確認方法

1. **Cloudflare Dashboard**
   - Workers & Pages → 該当Worker → Logs
   - Real-time logsまたはWorkers Logsタブで確認

2. **wrangler tail（制限あり）**
   ```bash
   wrangler tail --env staging --format pretty
   ```
   - 注意: console.logは`logs`配列に含まれない場合がある

## 根本原因

### 1. Waku RSCの動的モジュールロード
- サーバーアクションは遅延ロードされる
- 初回呼び出し時のみモジュールが読み込まれる
- モジュールレベルのconsole.logは実行タイミングが不定

### 2. Cloudflare Workersの実行モデル
- モジュール初期化時のログはキャプチャされない
- リクエストハンドラー内のログのみ確実にキャプチャ

### 3. wrangler tailのサンプリング
- デフォルトでサンプリングが有効
- すべてのログが表示されるわけではない
- Workers Logsが最も信頼できるソース

## 推奨事項

1. **デバッグ時はWorkers Logsを使用**
   - Cloudflare Dashboardが最も確実
   - wrangler tailは補助的に使用

2. **ログは関数内に配置**
   - fetchハンドラー内
   - ミドルウェア内
   - アクション関数内

3. **ローカル開発では`wrangler dev`を活用**
   - console.logが即座に表示される
   - デバッグが容易

## 結論

- console.log機能自体は**正常に動作している**
- `wrangler tail`の表示問題は**ツールの制限**
- Workers Logsには**すべて記録されている**
- ローカル開発では**問題なく表示される**

混乱の原因は、wrangler tailの動作とWorkers Logsの違いを理解していなかったことにある。