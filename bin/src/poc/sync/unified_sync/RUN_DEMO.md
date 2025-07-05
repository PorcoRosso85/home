# 複数ブラウザ同期デモ実行手順

## 1. WebSocketサーバー起動

```bash
cd /home/nixos/bin/src/poc/sync/unified_sync
nix develop . -c deno run --allow-net websocket-server.ts
```

## 2. HTTPサーバー起動（別ターミナル）

```bash
cd /home/nixos/bin/src/poc/sync/unified_sync
nix develop . -c deno run --allow-net --allow-read serve.ts
```

## 3. ブラウザでデモページを開く

1. ブラウザ1: http://localhost:3000/demo.html
2. ブラウザ2: http://localhost:3000/demo.html（別ウィンドウまたは別ブラウザ）

## 4. 同期テスト

1. ブラウザ1で「Create Random User」をクリック
2. ブラウザ2に自動的に同じユーザーが表示される
3. ブラウザ2で別のユーザーを作成
4. ブラウザ1に反映される

## 期待される動作

- 各ブラウザは独自のKuzuDB WASMインスタンスを持つ
- WebSocket経由でイベントが同期される
- 作成したユーザーには作成元のクライアントIDが表示される
- リアルタイムで双方向同期が行われる

## トラブルシューティング

### WebSocket接続エラー
- WebSocketサーバーが起動しているか確認
- ポート8080が使用されていないか確認

### KuzuDB初期化エラー
- ブラウザのコンソールでエラーを確認
- Cross-Origin Isolationが必要な場合は、serve.tsのヘッダーを確認

### 同期されない
- ネットワークタブでWebSocket通信を確認
- Event Logでメッセージの送受信を確認