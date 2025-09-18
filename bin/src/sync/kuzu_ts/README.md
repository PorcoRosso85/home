# KuzuDB Sync System

分散KuzuDBインスタンス間のWebSocketベース同期システム

## 概要

複数のKuzuDBインスタンス間でイベントソーシング方式による同期を実現するシステムです。

## ランタイムサポート

- **サーバー**: Deno（安定性、セキュリティ、標準準拠）
- **クライアント**: Bunランタイム専用
  - 高速起動、軽量実装、フルfeature対応

### ハイブリッドアプローチの理由

サーバーとクライアントで異なるランタイムを採用する理由：

1. **サーバー（Deno）**: 長時間稼働の信頼性とセキュリティを重視
   - プロダクション環境での実績
   - 標準Web APIへの準拠
   - セキュアなパーミッション管理

2. **クライアント（Bun）**: 開発体験と起動速度を重視
   - CLI操作での高速な起動時間
   - 開発者フレンドリーなAPI
   - 軽量な実装

この組み合わせにより、それぞれの強みを最大限に活用した最適なシステムを実現しています。

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
nix run .#bun-client

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
bun run server.ts

# クライアント起動
bun run bun_client.ts

# テスト実行
pytest tests/e2e_test.py -v
bun test
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
bun run examples/stats_monitoring.ts
```

統計ログの例：
```
=== DML Statistics Report ===
Overall: sent: 10, received: 5, applied: 4, failed: 1
Template: CREATE_USER - sent: 5, received: 3, applied: 3, success rate: 100%
Template: UPDATE_USER - sent: 3, received: 2, applied: 1, success rate: 50%
```

## 統一インターフェース

Bunランタイムでの使用方法：

```typescript
import { createSyncClient } from "./bun_client.ts";

const client = createSyncClient("ws://localhost:8080");
await client.connect();
await client.sendDML("CREATE USER {name: 'Alice'}");
```

### インターフェースの特徴

- **高速起動**: Bunの高速な起動時間を活用
- **自動再接続**: 接続断時の自動リトライ機能
- **統計収集**: DML操作の自動統計収集
- **型安全**: TypeScriptによる型定義

## 設定

環境変数：
- `PORT`: サーバーポート（デフォルト: 8080）
- `LOG_TS_PATH`: テレメトリモジュールパス