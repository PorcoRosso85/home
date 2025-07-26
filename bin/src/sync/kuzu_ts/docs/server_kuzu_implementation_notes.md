# サーバー側KuzuDB実装ノート

## 実装状況

サーバー側でKuzuDBインスタンスを持たせる設計と実装を完了しました。以下のコンポーネントが実装されています：

1. **ServerKuzuClient** (`core/server/server_kuzu_client.ts`)
   - サーバー環境でのKuzuDBインスタンス管理
   - イベント適用による状態同期
   - クエリ実行インターフェース

2. **WebSocketサーバー統合** (`core/websocket/server.ts`)
   - サーバー起動時にKuzuDBインスタンスを初期化
   - イベント受信時にサーバー側KuzuDBも更新
   - HTTPクエリエンドポイント `/query` の追加

3. **CLIツール** (`cli/query.ts`)
   - コマンドラインからサーバーにクエリを送信
   - 結果のテーブル/JSON形式出力

## 技術的制限事項

### KuzuDB WASM in Deno

現在の実装では、KuzuDB WASMがNode.js向けに作られているため、Denoでの実行時に以下の問題が発生します：

```
Error: Dynamic require of "fs" is not supported
```

これはKuzuDB WASMがNode.jsの`fs`モジュールを必要とするためです。

### 回避策

1. **Node.js互換レイヤーの使用**
   ```bash
   deno run --allow-all --node-modules-dir npm:kuzu-wasm
   ```

2. **別プロセスでの実行**
   - Node.jsプロセスでKuzuDBサーバーを実行
   - DenoからHTTP/WebSocket経由で通信

3. **将来的な対応**
   - KuzuDB WASMのDeno対応を待つ
   - またはDeno Node互換性の改善を待つ

## 使用方法

### サーバー起動（現在の制限下では動作しない）

```bash
deno run --allow-net --allow-read serve.ts
```

### CLIでのクエリ実行

```bash
# 基本的なクエリ
./cli/query.ts "MATCH (u:User) RETURN u"

# パラメータ付きクエリ
./cli/query.ts "MATCH (u:User {id: \$id}) RETURN u" -p '{"id": "user1"}'

# JSON出力
./cli/query.ts -j "MATCH (n) RETURN count(n) as count"
```

### プログラムからのクエリ実行

```typescript
async function queryServer(cypher: string, params?: Record<string, any>) {
  const response = await fetch("http://localhost:8080/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cypher, params })
  });
  
  const result = await response.json();
  if (!result.success) {
    throw new Error(result.error);
  }
  
  return result.data;
}

// 使用例
const users = await queryServer("MATCH (u:User) RETURN u");
```

## 代替アプローチ

### Option 1: Node.jsサブプロセス

```typescript
// Node.jsでKuzuDBサーバーを実行
const kuzuServer = new Deno.Command("node", {
  args: ["kuzu-server.js"],
  stdout: "piped",
  stderr: "piped",
});

const process = kuzuServer.spawn();
```

### Option 2: 別サービスとして実装

1. Node.jsでKuzuDBサービスを実装
2. REST APIまたはgRPCで通信
3. Denoからはクライアントとして接続

### Option 3: ブラウザ経由のクエリ

現在の実装では、各ブラウザクライアントがKuzuDBインスタンスを持っています。
特定のクライアントを「マスター」として指定し、そのクライアント経由でクエリを実行することも可能です。

## 今後の展望

1. **Deno対応の改善**
   - KuzuDB WASMのDeno対応版の開発
   - またはDenoのNode.js互換性向上を待つ

2. **ハイブリッドアプローチ**
   - 読み取り専用クエリはクライアント側で実行
   - 集約クエリや分析はサーバー側で実行

3. **パフォーマンス最適化**
   - クエリ結果のキャッシング
   - インデックスの最適化
   - 並列クエリ実行

## まとめ

設計と実装は完了していますが、KuzuDB WASMのDeno互換性の問題により、現在は動作しません。
この問題は技術的な制限であり、以下のいずれかの対応が必要です：

1. KuzuDB WASMのDeno対応を待つ
2. Node.jsベースの別サービスとして実装
3. クライアント側のKuzuDBインスタンスを活用した代替アプローチ

実装されたコードは、将来的にKuzuDB WASMがDeno対応した際にそのまま使用可能です。