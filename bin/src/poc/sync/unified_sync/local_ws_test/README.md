# Local WebSocket Client-Server Test

非ブラウザ環境でのWebSocket通信統合テスト

## 実行方法
```bash
nix run .#test
```

## 現在の状態
- ✅ 正常動作
- WebSocketサーバー機能が検証済み

## テスト内容
1. WebSocketサーバー起動（ポート8081）
2. 複数クライアント接続
3. イベントブロードキャスト確認
4. 履歴同期機能確認
5. 同時接続処理確認

## 成功条件
- Client1からのイベントをClient2が受信
- 新規クライアントが過去の履歴を取得
- 10クライアント同時接続が可能