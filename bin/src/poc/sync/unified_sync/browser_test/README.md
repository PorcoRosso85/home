# Browser WASM Client-Server Test

ブラウザ環境でのKuzuDB WASM + WebSocket統合テスト

## 実行方法
```bash
nix run .#test
```

## 現在の状態
- ⚠️ ブラウザ依存関係不足のため失敗
- libgbm.so.1, libudev.so.1が不足
- テストはスキップされる

## テスト内容
1. WebSocketサーバー起動（ポート8080）
2. HTTPサーバー起動（ポート3000）
3. Playwrightでブラウザテスト実行
4. KuzuDB WASM初期化確認
5. リアルタイム同期確認