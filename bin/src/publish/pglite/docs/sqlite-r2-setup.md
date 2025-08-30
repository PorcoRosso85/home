# SQLite + R2 Setup Guide

R2にSQLiteデータベースをホストして、ブラウザ上で直接クエリを実行する方法。

## アーキテクチャ

```
Browser → SQLite WASM → Fetch DB from R2 → Execute Query
           ↑
     sql.js/sqlite3.js
```

## ローカル開発

### R2エミュレーション
```bash
# ローカルでR2をエミュレート（.wrangler/state/に保存）
npm run dev

# 実際のCloudflare R2を使用
npm run dev:remote
```

### データベースアップロード（ローカル）
```bash
# ローカルR2にSQLiteデータベースをアップロード
curl -X POST http://localhost:8787/api/sqlite/upload \
  -F "database=@sample.db" \
  -F "name=sample.db"

# データベース一覧を取得
curl http://localhost:8787/api/sqlite/list

# データベースを取得
curl http://localhost:8787/api/sqlite/db/sample.db -o downloaded.db
```

## 本番環境

### R2バケット作成
```bash
# R2バケットを作成
wrangler r2 bucket create waku-data

# SQLiteデータベースをアップロード
wrangler r2 object put waku-data/sqlite-databases/prod.db --file=./prod.db
```

### デプロイ
```bash
# Workersにデプロイ
npm run deploy
```

## API エンドポイント

### POST /api/sqlite/upload
SQLiteデータベースをR2にアップロード

```javascript
const formData = new FormData();
formData.append('database', file);
formData.append('name', 'mydb.sqlite');

fetch('/api/sqlite/upload', {
  method: 'POST',
  body: formData
});
```

### GET /api/sqlite/list
R2内のデータベース一覧を取得

```javascript
fetch('/api/sqlite/list')
  .then(res => res.json())
  .then(data => console.log(data.databases));
```

### GET /api/sqlite/db/{name}
特定のデータベースを取得

```javascript
fetch('/api/sqlite/db/mydb.sqlite')
  .then(res => res.arrayBuffer())
  .then(buffer => {
    // Use with sql.js
    const db = new SQL.Database(new Uint8Array(buffer));
  });
```

### DELETE /api/sqlite/db/{name}
データベースを削除

```javascript
fetch('/api/sqlite/db/mydb.sqlite', {
  method: 'DELETE'
});
```

## フロントエンド使用例

```tsx
import { SQLiteR2Manager } from '@/components/sqlite-r2-manager';

export default function App() {
  return (
    <div>
      <h1>SQLite + R2 Demo</h1>
      <SQLiteR2Manager />
    </div>
  );
}
```

## セキュリティ考慮事項

1. **アップロード制限**: ファイルサイズ制限を設定
2. **認証**: 本番環境ではアップロードAPIに認証を追加
3. **CORS**: 必要に応じてCORS設定を調整
4. **バリデーション**: SQLiteファイルのマジックバイトを検証

## パフォーマンス最適化

1. **キャッシュ**: データベースをブラウザキャッシュに保存
2. **圧縮**: 大きなデータベースはgzip圧縮して転送
3. **分割読み込み**: 必要な部分のみを読み込む（Range requests）

## トラブルシューティング

### ローカルでR2が動作しない
```bash
# .wrangler/state/を削除して再起動
rm -rf .wrangler/state/
npm run dev
```

### WASMが読み込めない
```bash
# public/wasm/にsql.jsファイルがあることを確認
ls -la public/wasm/
# sqlite3.js, sqlite3.wasm が存在するか確認
```

### データベースが大きすぎる
- Workers無料プランは10MBまで
- 有料プランは100MBまで
- より大きなデータベースはRange requestsで部分読み込み