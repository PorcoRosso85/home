# Raft Consensus Algorithm

## 概要

分散システムにおける合意形成のためのRaftアルゴリズムの簡略実装です。

## 機能

- **リーダー選出**: 自動的にリーダーを選出
- **ログレプリケーション**: 全ノードにデータを複製
- **フォルトトレランス**: N/2までの障害に耐性

## 使用方法

```typescript
import { RaftCluster, ServiceRegistryRaft } from "./mod.ts";

// 3ノードクラスターの作成
const cluster = new RaftCluster();
await cluster.addNode("node-1", "localhost:5001");
await cluster.addNode("node-2", "localhost:5002");
await cluster.addNode("node-3", "localhost:5003");

// クラスター開始
await cluster.start();

// サービスレジストリの使用
const registry = new ServiceRegistryRaft(cluster);
await registry.register({
  id: "api-1",
  name: "api",
  host: "localhost",
  port: 8080
});
```

## テスト

```bash
deno test raft.test.ts
```