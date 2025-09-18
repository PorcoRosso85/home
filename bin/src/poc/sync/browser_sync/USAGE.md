# Browser Sync POC 使用方法

## 起動方法

```bash
cd /home/nixos/bin/src/poc/sync/browser_sync
nix develop --command deno task dev
```

## テスト方法

1. サーバーが起動したら、ブラウザで http://localhost:8080 を開く
2. 別のブラウザやタブで同じURLを開く（複数可）
3. 以下の機能をテスト：

### 共有テキストエディタ
- どちらかのブラウザでテキストを入力
- 他のブラウザでリアルタイムに反映されることを確認

### 共有TODOリスト
- TODOを追加、チェック、削除
- すべてのブラウザで同期されることを確認

### ネットワーク耐性テスト
- ブラウザの開発者ツールでネットワークをオフラインに
- 操作を続ける
- オンラインに戻すと自動再接続

## アーキテクチャ

```
Browser A ←→ WebSocket ←→ Deno Server (LocalSyncServer) ←→ WebSocket ←→ Browser B
                                    ↓
                              Event History
                              Vector Clock
                              Conflict Resolution
```

## 特徴

- **自動再接続**: 3秒ごとに再接続試行
- **楽観的更新**: ローカルで即座に反映
- **競合解決**: Last Write Winsで自動解決
- **イベントログ**: 同期の様子を可視化

## カスタマイズ

`client.js`の`debounce`時間を調整して、同期頻度を変更可能：
```javascript
this.debounce(() => {
    // 300ms → 100ms で高速化
}, 100)
```