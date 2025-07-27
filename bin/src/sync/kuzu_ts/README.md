# KuzuDB Sync System

分散KuzuDBインスタンス間のWebSocketベース同期システム

## 概要

複数のKuzuDBインスタンス間でイベントソーシング方式による同期を実現するシステムです。

### 主な機能

- **リアルタイム同期**: WebSocketによる低遅延同期
- **イベントソーシング**: 全ての変更をイベントとして記録
- **アーカイブ機能**: 30日経過イベントのS3自動アーカイブ
- **集計キャッシュ**: 高速クエリのためのO(1)アクセス
- **テレメトリ統合**: OpenTelemetry準拠のログ

## クイックスタート

```bash
# サーバー起動
nix run .#server

# クライアント起動（別ターミナル）
nix run .#client

# テスト実行
nix run .#test
```

## アーキテクチャ

```
Client A → WebSocket → Server → KuzuDB
                          ↓
                    Broadcast
                          ↓
                    Client B, C...
```

### コンポーネント

1. **サーバー** (`server.ts`)
   - ポート8080でWebSocket接続を待機
   - イベントの永続化とブロードキャスト

2. **クライアント** (`client.ts`)
   - 対話的なイベント送信
   - リアルタイム同期の確認

3. **ストレージ** (`storage/`)
   - ローカルストレージとS3の統合
   - 自動アーカイブポリシー

## 開発

```bash
# 開発環境
nix develop

# サーバー起動（デバッグモード）
deno run --allow-net --allow-read --allow-env server.ts

# テスト実行
pytest tests/e2e_test.py -v
deno test tests/ --allow-all
```

## 設定

環境変数：
- `PORT`: サーバーポート（デフォルト: 8080）
- `LOG_TS_PATH`: テレメトリモジュールパス