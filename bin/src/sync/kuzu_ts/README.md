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
- **統計モニタリング**: DML操作の自動統計収集と定期レポート

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

## 統計モニタリング

SyncKuzuClientは自動的にDML操作の統計を収集し、5秒ごとにレポートします。

### 機能

1. **定期統計レポート**
   - 5秒ごとに自動的にDML統計をログ出力
   - 全体統計とテンプレート別統計を含む

2. **テンプレート別カウンター**
   - 各テンプレート（CREATE_USER、UPDATE_USER等）ごとの統計
   - sent、received、applied、failed のカウント
   - 成功率の自動計算

3. **詳細統計API**
   ```typescript
   // 全体統計の取得
   const stats = client.getDMLStats();
   
   // テンプレート別詳細統計の取得
   const detailedStats = client.getDetailedStatsByTemplate();
   ```

### 使用例

```bash
# 統計モニタリングのデモ実行
deno run --allow-net --allow-read examples/stats_monitoring.ts
```

統計ログの例：
```
=== DML Statistics Report ===
Overall: sent: 10, received: 5, applied: 4, failed: 1
Template: CREATE_USER - sent: 5, received: 3, applied: 3, success rate: 100%
Template: UPDATE_USER - sent: 3, received: 2, applied: 1, success rate: 50%
```

## 設定

環境変数：
- `PORT`: サーバーポート（デフォルト: 8080）
- `LOG_TS_PATH`: テレメトリモジュールパス