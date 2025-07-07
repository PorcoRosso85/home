import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, afterEach } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { createCausalSyncClient, disconnect } from './causal-sync-client.ts';
import type { CausalSyncClient, CausalOperation } from './causal-sync-client.ts';

describe("Causal Ordering Sync Tests", () => {
  let allClients: CausalSyncClient[] = [];
  
  afterEach(async () => {
    // すべてのクライアントを確実に切断
    for (const client of allClients) {
      try {
        await disconnect(client);
      } catch (e) {
        // エラーを無視
      }
    }
    allClients = [];
    
    // WebSocketが完全にクローズされるのを待つ
    await new Promise(resolve => setTimeout(resolve, 200));
  });
  it("should handle concurrent increments with causal ordering", async () => {
    console.log('🔴 TDD Red: Testing concurrent increments with causal ordering');
    
    const clients: CausalSyncClient[] = [];
    const clientCount = 5;
    
    // 5つのクライアントを初期化
    for (let i = 0; i < clientCount; i++) {
      const client = await createCausalSyncClient({
        clientId: `causal-client-${i}`,
        dbPath: ':memory:',
        wsUrl: 'ws://localhost:8083'
      });
      clients.push(client);
      allClients.push(client);
    }
    
    console.log('✅ All clients connected');
    
    // Step 1: Client 0がカウンターを作成
    const createOp = await clients[0].executeOperation({
      id: 'create-counter',
      dependsOn: [],
      type: 'CREATE',
      payload: {
        cypherQuery: "CREATE (c:Counter {id: 'shared-counter', value: 0})"
      },
      clientId: clients[0].id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Step 2: 全クライアントが同時にインクリメント（因果関係を明示）
    console.log('\n📊 All clients incrementing counter...');
    const incrementOps: Promise<CausalOperation>[] = [];
    
    for (let i = 0; i < clientCount; i++) {
      incrementOps.push(
        clients[i].executeOperation({
          id: `increment-${i}`,
          dependsOn: ['create-counter'], // 明示的に作成操作に依存
          type: 'INCREMENT',
          payload: {
            nodeId: 'shared-counter',
            property: 'value',
            delta: 1
          },
          clientId: clients[i].id,
          timestamp: Date.now()
        })
      );
    }
    
    await Promise.all(incrementOps);
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Step 3: 結果を検証 - すべてのインクリメントが適用されているはず
    console.log('\n🔍 Verifying final counter values...');
    for (let i = 0; i < clientCount; i++) {
      const result = await clients[i].query(`
        MATCH (c:Counter {id: 'shared-counter'})
        RETURN c.value as value
      `);
      
      assertEquals(result[0].value, 5, `Client ${i} should see counter value as 5`);
      console.log(`✅ Client ${i}: counter = ${result[0].value}`);
    }
    
    // クリーンアップはafterEachで実行
  });

  it("should resolve conflicting updates based on causal dependencies", async () => {
    console.log('\n🔴 TDD Red: Testing conflicting updates with causal ordering');
    
    const client1 = await createCausalSyncClient({
      clientId: 'conflict-client-1',
      dbPath: ':memory:',
      wsUrl: 'ws://localhost:8083'
    });
    allClients.push(client1);
    
    const client2 = await createCausalSyncClient({
      clientId: 'conflict-client-2',
      dbPath: ':memory:',
      wsUrl: 'ws://localhost:8083'
    });
    allClients.push(client2);
    
    // 初期ノードを作成
    await client1.executeOperation({
      id: 'create-node',
      dependsOn: [],
      type: 'CREATE',
      payload: {
        cypherQuery: "CREATE (n:Node {id: 'test-node', status: 'initial'})"
      },
      clientId: client1.id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 両クライアントが異なる更新を実行
    const update1Promise = client1.executeOperation({
      id: 'update-1',
      dependsOn: ['create-node'],
      type: 'UPDATE',
      payload: {
        cypherQuery: "MATCH (n:Node {id: 'test-node'}) SET n.status = 'client1-updated'"
      },
      clientId: client1.id,
      timestamp: Date.now()
    });
    
    const update2Promise = client2.executeOperation({
      id: 'update-2',
      dependsOn: ['create-node'],
      type: 'UPDATE',
      payload: {
        cypherQuery: "MATCH (n:Node {id: 'test-node'}) SET n.status = 'client2-updated'"
      },
      clientId: client2.id,
      timestamp: Date.now() + 10 // わずかに後
    });
    
    await Promise.all([update1Promise, update2Promise]);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 両クライアントで同じ結果を確認（Last-Write-Wins）
    const result1 = await client1.query("MATCH (n:Node {id: 'test-node'}) RETURN n.status as status");
    const result2 = await client2.query("MATCH (n:Node {id: 'test-node'}) RETURN n.status as status");
    
    assertEquals(result1[0].status, result2[0].status, "Both clients should see the same status");
    console.log(`✅ Consistent state: ${result1[0].status}`);
    
    // クリーンアップはafterEachで実行
  });

  it("should wait for dependencies before applying operations", async () => {
    console.log('\n🔴 TDD Red: Testing dependency waiting mechanism');
    
    const client = await createCausalSyncClient({
      clientId: 'dependency-client',
      dbPath: ':memory:',
      wsUrl: 'ws://localhost:8083'
    });
    allClients.push(client);
    
    // 依存関係のある操作を逆順で送信
    const op3Promise = client.executeOperation({
      id: 'op-3',
      dependsOn: ['op-2'], // op-2に依存
      type: 'UPDATE',
      payload: {
        cypherQuery: "MATCH (n:Chain {id: 'chain'}) SET n.step = 3"
      },
      clientId: client.id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const op2Promise = client.executeOperation({
      id: 'op-2',
      dependsOn: ['op-1'], // op-1に依存
      type: 'UPDATE',
      payload: {
        cypherQuery: "MATCH (n:Chain {id: 'chain'}) SET n.step = 2"
      },
      clientId: client.id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const op1Promise = client.executeOperation({
      id: 'op-1',
      dependsOn: [], // 依存なし
      type: 'CREATE',
      payload: {
        cypherQuery: "CREATE (n:Chain {id: 'chain', step: 1})"
      },
      clientId: client.id,
      timestamp: Date.now()
    });
    
    // すべての操作が正しい順序で適用されるのを待つ
    await Promise.all([op1Promise, op2Promise, op3Promise]);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 最終状態を確認
    const result = await client.query("MATCH (n:Chain {id: 'chain'}) RETURN n.step as step");
    assertEquals(result[0].step, 3, "Final step should be 3");
    console.log(`✅ Operations applied in correct order: step = ${result[0].step}`);
    
    // 操作履歴を確認
    const history = await client.getOperationHistory();
    assertEquals(history[0].id, 'op-1', "First operation should be op-1");
    assertEquals(history[1].id, 'op-2', "Second operation should be op-2");
    assertEquals(history[2].id, 'op-3', "Third operation should be op-3");
    console.log('✅ Operation history:', history.map(op => op.id));
    
    // クリーンアップはafterEachで実行
  });
});