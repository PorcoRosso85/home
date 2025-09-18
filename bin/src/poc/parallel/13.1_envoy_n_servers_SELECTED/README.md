# POC 13.1: Envoy N Servers Extension

## 🎯 概要

POC 12の2台固定Envoyプロキシを、N台の動的サーバー構成に拡張。環境変数でサーバーリストを指定可能にし、基本的な負荷分散を実現。

## 🔄 POC 12からの進化

**POC 12（固定2台）:**
```typescript
const BACKEND_SERVERS = [
  { id: "server-1", url: "http://localhost:4001" },
  { id: "server-2", url: "http://localhost:4002" }
];
```

**POC 13.1（N台対応）:**
```typescript
// 環境変数から動的に読み込み
const BACKEND_SERVERS = parseServers(Deno.env.get("BACKEND_SERVERS"));
// BACKEND_SERVERS=server1:4001,server2:4002,server3:4003,...
```

## 📋 実装内容

### 1. **動的サーバーリスト**
```typescript
interface ServerConfig {
  servers: string; // "host1:port1,host2:port2,..."
  strategy: "round-robin" | "random" | "least-conn";
}
```

### 2. **改良されたヘルスチェック**
```typescript
// N台すべてを並行チェック
async function checkAllServers(): Promise<HealthStatus[]> {
  return Promise.all(
    servers.map(server => checkHealth(server))
  );
}
```

### 3. **負荷分散戦略**
- Round Robin（デフォルト）
- Random
- Least Connections（接続数追跡）

## 🏗️ アーキテクチャ

```
         Clients
            │
            ▼
   ┌────────────────┐
   │  Envoy Proxy  │
   │   (port 8080) │
   └───────┬────────┘
           │
    環境変数で設定
    BACKEND_SERVERS=
           │
   ┌───────┼───────┬─────── ─ ─ ─
   ▼       ▼       ▼
Server1  Server2  Server3  ...  ServerN
(:4001)  (:4002)  (:4003)      (:400N)
```

## 📝 実装ファイル

### envoy-n-servers.ts
```typescript
// 環境変数からサーバーリストを解析
function parseServers(serversStr: string): ServerInfo[] {
  if (!serversStr) {
    throw new Error("BACKEND_SERVERS environment variable is required");
  }
  
  return serversStr.split(",").map((serverStr, index) => {
    const [host, port] = serverStr.split(":");
    return {
      id: `server-${index + 1}`,
      url: `http://${host}:${port}`,
      host,
      port: parseInt(port),
      healthy: true,
      connections: 0
    };
  });
}

// メイン処理
const BACKEND_SERVERS = parseServers(
  Deno.env.get("BACKEND_SERVERS") || "localhost:4001,localhost:4002,localhost:4003"
);

const STRATEGY = Deno.env.get("LB_STRATEGY") || "round-robin";

console.log(`🔄 Envoy Proxy started with ${BACKEND_SERVERS.length} backends`);
console.log(`📊 Load balancing strategy: ${STRATEGY}`);

// 既存のPOC 12のコードを拡張...
```

## 🧪 テストケース

### 基本的な動作確認
```bash
# 3サーバー構成で起動
export BACKEND_SERVERS="localhost:4001,localhost:4002,localhost:4003"
deno run --allow-net --allow-env envoy-n-servers.ts

# 5サーバー構成
export BACKEND_SERVERS="srv1:5001,srv2:5002,srv3:5003,srv4:5004,srv5:5005"
```

### 負荷分散の検証
```bash
# 1000リクエストを送信して分散を確認
./test-load-distribution.sh 1000

# 期待される出力:
# server-1: 333 requests (33.3%)
# server-2: 334 requests (33.4%)
# server-3: 333 requests (33.3%)
```

## 🚀 実行方法

### 1. テストサーバーをN台起動
```bash
# start-n-servers.sh
#!/bin/bash
N=${1:-3}  # デフォルト3台

for i in $(seq 1 $N); do
  PORT=$((4000 + i))
  SERVER_NAME="server-$i" PORT=$PORT deno run --allow-net --allow-env test-server.ts &
  echo "Started server-$i on port $PORT"
done
```

### 2. Envoyプロキシ起動
```bash
# サーバーリストを環境変数で指定
BACKEND_SERVERS="localhost:4001,localhost:4002,localhost:4003" \
deno run --allow-net --allow-env envoy-n-servers.ts
```

### 3. 動的追加のシミュレーション
```bash
# 新しいサーバーを追加してEnvoyを再起動
# （13.2で真の動的追加を実装）
```

## 📊 期待される成果

1. **柔軟な構成**: 2台からN台まで自由に設定
2. **均等な負荷分散**: N台に均等に分散
3. **障害耐性**: 1台が落ちても残りで継続

## 🔗 次のステップ

**POC 13.2**: サービスディスカバリーで真の動的管理
- 再起動なしでサーバー追加/削除
- 自動的な障害検出と除外
- より高度なルーティング戦略

**POC 13.3**: Consistent Hashingの統合
- キーベースの一貫したルーティング
- サーバー追加時の影響最小化