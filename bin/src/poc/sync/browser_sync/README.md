# Browser Sync POC

local_syncエンジンを使用して、WebSocket経由で複数ブラウザ間のリアルタイム同期を実現するPOC。

## 目的

- 実際のブラウザ間でのリアルタイム同期
- WebSocketによる双方向通信
- ネットワーク遅延や切断への対応
- 実用的なUIでの動作確認

## アーキテクチャ

```
Browser A ─┐
           ├─→ WebSocket ─→ Deno Server (LocalSyncServer)
Browser B ─┘                     ↓
                          State & Events
```

## 実装内容

1. **サーバー側** (`server.ts`)
   - WebSocketサーバー
   - LocalSyncServerの統合
   - 接続管理

2. **クライアント側** (`client.html`)
   - WebSocket接続
   - 自動再接続
   - UIでの操作と表示

3. **共有ドキュメント例**
   - テキストエディタ
   - TODOリスト
   - 描画キャンバス

## 技術スタック

- Deno (サーバー)
- WebSocket
- Vanilla JS (クライアント)
- LocalSyncServer (同期エンジン)