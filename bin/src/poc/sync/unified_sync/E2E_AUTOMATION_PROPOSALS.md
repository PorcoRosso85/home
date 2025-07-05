# E2E自動化シミュレーション方法の提案

## 案1: KuzuDB Node.js版による擬似ブラウザ環境

### 概要
- 各「ブラウザ」をNode.jsプロセスとして実行
- KuzuDB Node.js版（CommonJS）を使用
- WebSocket通信は実際に行う

### 実装案
```typescript
// pseudo-browser-client.ts
import { KuzuNodeStorage } from './kuzu_storage.cts';

class PseudoBrowserClient {
  private storage: KuzuNodeStorage;
  private ws: WebSocket;
  
  async initialize(clientId: string) {
    // KuzuDB Node.js版を初期化
    this.storage = new KuzuNodeStorage();
    await this.storage.initialize();
    
    // WebSocket接続
    this.ws = new WebSocket(`ws://localhost:8080?clientId=${clientId}`);
  }
  
  async simulateBrowserBehavior() {
    // ブラウザの動作をシミュレート
  }
}
```

### メリット
- ✅ 実際のKuzuDBを使用（モックなし）
- ✅ 複数プロセスで並行実行可能
- ✅ CI/CDで実行可能

### デメリット
- ⚠️ ブラウザ版と完全互換ではない
- ⚠️ WebAssembly特有の問題を検出できない

## 案2: Dockerコンテナによる完全自動化

### 概要
- Dockerコンテナ内でブラウザとサーバーを実行
- docker-composeで全体を管理
- ヘッドレスブラウザで自動実行

### 実装案
```yaml
# docker-compose.yml
version: '3.8'
services:
  websocket-server:
    build: .
    ports:
      - "8080:8080"
    command: deno run --allow-net websocket-server.ts
  
  http-server:
    build: .
    ports:
      - "3000:3000"
    command: deno run --allow-net --allow-read serve.ts
    
  test-runner:
    build: .
    depends_on:
      - websocket-server
      - http-server
    command: npx playwright test --reporter=json
    volumes:
      - ./test-results:/app/test-results
```

### メリット
- ✅ 完全に自動化可能
- ✅ 再現性が高い
- ✅ CI/CDに最適

### デメリット
- ⚠️ セットアップが複雑
- ⚠️ デバッグが困難

## 案3: ハイブリッドアプローチ（推奨）

### 概要
- レイヤーを分離してテスト
- 各レイヤーで適切な方法を選択

### 実装案

#### Layer 1: 通信層テスト（Node.jsで実行）
```typescript
// test-communication-layer.ts
import { assertEquals } from "jsr:@std/assert@^1.0.0";

Deno.test("通信層: イベントブロードキャスト", async () => {
  const server = await startTestServer();
  const client1 = await connectToServer("client1");
  const client2 = await connectToServer("client2");
  
  const received: any[] = [];
  client2.onEvent(e => received.push(e));
  
  await client1.sendEvent(testEvent);
  await waitFor(() => received.length > 0);
  
  assertEquals(received[0].id, testEvent.id);
});
```

#### Layer 2: KuzuDB操作テスト（Node.js版で代替）
```typescript
// test-kuzu-operations.ts
Deno.test("KuzuDB操作: Cypherクエリ実行", async () => {
  const storage = new KuzuNodeStorage();
  await storage.initialize();
  
  // テンプレート実行
  await storage.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice"
  });
  
  const users = await storage.query("MATCH (u:User) RETURN u");
  assertEquals(users.length, 1);
});
```

#### Layer 3: 統合テスト（軽量ブラウザ環境）
```typescript
// test-integration-lightweight.ts
import { chromium } from 'playwright';

Deno.test("軽量統合: 最小限のブラウザテスト", async () => {
  // サーバー自動起動
  const servers = await startAllServers();
  
  // ヘッドレスモードで高速実行
  const browser = await chromium.launch({
    headless: true,
    args: ['--disable-gpu', '--no-sandbox']
  });
  
  // 重要な統合ポイントのみテスト
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/test-minimal.html');
  
  const result = await page.evaluate(async () => {
    // 最小限のKuzuDB操作を確認
    return await window.testMinimalSync();
  });
  
  assert(result.success);
});
```

### メリット
- ✅ 各層で適切な方法を選択
- ✅ 高速実行可能
- ✅ 問題の切り分けが容易

## 案4: Service Workerによるブラウザ内完結テスト

### 概要
- Service Workerで仮想サーバーを実装
- 単一ブラウザ内で複数クライアントをシミュレート

### 実装案
```typescript
// service-worker-mock-server.js
self.addEventListener('fetch', event => {
  if (event.request.url.includes('/ws')) {
    // WebSocket通信をシミュレート
    event.respondWith(handleWebSocketSimulation(event.request));
  }
});

// test-with-service-worker.html
<script>
  // 複数のKuzuDBインスタンスを作成
  const client1 = new KuzuClient('client1');
  const client2 = new KuzuClient('client2');
  
  // Service Worker経由で通信
  await client1.sync();
  await client2.sync();
</script>
```

### メリット
- ✅ ブラウザ環境で完結
- ✅ 実際のKuzuDB WASMを使用
- ✅ デバッグが容易

### デメリット
- ⚠️ 実際のWebSocket通信ではない
- ⚠️ Service Workerの制約

## 推奨実装順序

### Phase 1: ハイブリッドアプローチの基本実装
1. 通信層テストの自動化
2. KuzuDB操作層のNode.js版テスト
3. 最小限の統合テスト

### Phase 2: Docker環境の構築
1. docker-compose設定
2. CI/CDパイプライン構築
3. 定期実行の設定

### Phase 3: 本番相当のE2Eテスト
1. フルブラウザテスト（月次）
2. 負荷テスト（リリース前）
3. セキュリティテスト

この段階的アプローチにより、開発速度を保ちながら品質を担保できます。