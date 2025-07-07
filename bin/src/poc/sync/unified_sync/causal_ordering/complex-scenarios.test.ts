import { assertEquals, assertExists, assertRejects } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, afterEach } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { createCausalSyncClient, disconnect } from './causal-sync-client.ts';
import type { CausalSyncClient, CausalOperation } from './causal-sync-client.ts';

describe("Complex Causal Ordering Scenarios", () => {
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
  it("should handle diamond-shaped dependency graph", async () => {
    console.log('🔴 TDD Red: Testing diamond dependency graph');
    
    const client = await createCausalSyncClient({
      clientId: 'diamond-client',
      dbPath: ':memory:',
      wsUrl: 'ws://localhost:8083'
    });
    allClients.push(client);
    
    // ダイヤモンド形状の依存関係グラフ
    //    A
    //   / \
    //  B   C
    //   \ /
    //    D
    
    // 逆順で送信
    const opD = await client.executeOperation({
      id: 'op-D',
      dependsOn: ['op-B', 'op-C'], // BとCの両方に依存
      type: 'UPDATE',
      payload: {
        cypherQuery: "MATCH (n:Diamond {id: 'node'}) SET n.step = 'D'"
      },
      clientId: client.id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const opC = await client.executeOperation({
      id: 'op-C',
      dependsOn: ['op-A'],
      type: 'UPDATE',
      payload: {
        cypherQuery: "MATCH (n:Diamond {id: 'node'}) SET n.step = 'C'"
      },
      clientId: client.id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const opB = await client.executeOperation({
      id: 'op-B',
      dependsOn: ['op-A'],
      type: 'UPDATE',
      payload: {
        cypherQuery: "MATCH (n:Diamond {id: 'node'}) SET n.step = 'B'"
      },
      clientId: client.id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const opA = await client.executeOperation({
      id: 'op-A',
      dependsOn: [],
      type: 'CREATE',
      payload: {
        cypherQuery: "CREATE (n:Diamond {id: 'node', step: 'A'})"
      },
      clientId: client.id,
      timestamp: Date.now()
    });
    
    // 操作が適用されるのを待つ（より長い待機時間）
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 最終状態はD
    const result = await client.query("MATCH (n:Diamond {id: 'node'}) RETURN n.step as step");
    assertEquals(result[0].step, 'D', "Final step should be D");
    
    // 操作履歴の順序を確認
    const history = await client.getOperationHistory();
    const ids = history.map(op => op.id);
    assertEquals(ids.length, 4, "Should have 4 operations");
    assertEquals(ids[0], 'op-A', "First operation should be A");
    assertEquals(ids[ids.length - 1], 'op-D', "Last operation should be D");
    
    // クリーンアップはafterEachで実行
  });

  it("should detect and handle circular dependencies", async () => {
    console.log('\n🔴 TDD Red: Testing circular dependency detection');
    
    const client = await createCausalSyncClient({
      clientId: 'circular-client',
      dbPath: ':memory:',
      wsUrl: 'ws://localhost:8083'
    });
    allClients.push(client);
    
    // 循環依存: A → B → C → A
    const operations = [
      {
        id: 'op-A',
        dependsOn: ['op-C'], // Cに依存（循環）
        type: 'CREATE' as const,
        payload: { cypherQuery: "CREATE (n:Circular {id: 'A'})" },
        clientId: client.id,
        timestamp: Date.now()
      },
      {
        id: 'op-B',
        dependsOn: ['op-A'],
        type: 'CREATE' as const,
        payload: { cypherQuery: "CREATE (n:Circular {id: 'B'})" },
        clientId: client.id,
        timestamp: Date.now() + 1
      },
      {
        id: 'op-C',
        dependsOn: ['op-B'],
        type: 'CREATE' as const,
        payload: { cypherQuery: "CREATE (n:Circular {id: 'C'})" },
        clientId: client.id,
        timestamp: Date.now() + 2
      }
    ];
    
    // 操作を送信
    for (const op of operations) {
      await client.executeOperation(op);
    }
    
    // タイムアウトを設定して待つ
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 循環依存のため、どの操作も適用されていないはず
    const result = await client.query("MATCH (n:Circular) RETURN count(n) as count");
    assertEquals(result[0].count, 0, "No operations should be applied due to circular dependency");
    
    // 循環依存が検出されたことを確認
    const circularDetected = await client.getCircularDependencies();
    assertExists(circularDetected, "Circular dependencies should be detected");
    assertEquals(circularDetected.length, 1, "One circular dependency cycle should be found");
    assertEquals(circularDetected[0].sort(), ['op-A', 'op-B', 'op-C'].sort(), 
      "Circular dependency should include all three operations");
    
    // クリーンアップはafterEachで実行
  });

  it("should handle network partition and reconciliation", async () => {
    console.log('\n🔴 TDD Red: Testing network partition and reconciliation');
    
    // 2つのグループに分かれたクライアント
    const group1Clients: CausalSyncClient[] = [];
    const group2Clients: CausalSyncClient[] = [];
    
    // Group 1: 3クライアント
    for (let i = 0; i < 3; i++) {
      const client = await createCausalSyncClient({
        clientId: `partition-g1-${i}`,
        dbPath: ':memory:',
        wsUrl: 'ws://localhost:8083'
      });
      allClients.push(client);
      group1Clients.push(client);
    }
    
    // Group 2: 2クライアント
    for (let i = 0; i < 2; i++) {
      const client = await createCausalSyncClient({
        clientId: `partition-g2-${i}`,
        dbPath: ':memory:',
        wsUrl: 'ws://localhost:8083'
      });
      allClients.push(client);
      group2Clients.push(client);
    }
    
    // 初期状態を作成
    await group1Clients[0].executeOperation({
      id: 'init',
      dependsOn: [],
      type: 'CREATE',
      payload: {
        cypherQuery: "CREATE (n:PartitionTest {id: 'shared', value: 0, lastGroup: 'init'})"
      },
      clientId: group1Clients[0].id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // ネットワーク分断をシミュレート
    console.log('📡 Simulating network partition...');
    
    // Group 1とGroup 2を分離
    await group1Clients[0].simulatePartition(['partition-g1-0', 'partition-g1-1', 'partition-g1-2']);
    await group2Clients[0].simulatePartition(['partition-g2-0', 'partition-g2-1']);
    
    // 各グループで異なる操作を実行
    // Group 1: valueを100に設定
    await group1Clients[0].executeOperation({
      id: 'group1-update',
      dependsOn: ['init'],
      type: 'UPDATE',
      payload: {
        cypherQuery: "MATCH (n:PartitionTest {id: 'shared'}) SET n.value = 100, n.lastGroup = 'group1'"
      },
      clientId: group1Clients[0].id,
      timestamp: Date.now() + 1000
    });
    
    // Group 2: valueを200に設定
    await group2Clients[0].executeOperation({
      id: 'group2-update',
      dependsOn: ['init'],
      type: 'UPDATE',
      payload: {
        cypherQuery: "MATCH (n:PartitionTest {id: 'shared'}) SET n.value = 200, n.lastGroup = 'group2'"
      },
      clientId: group2Clients[0].id,
      timestamp: Date.now() + 2000 // タイムスタンプが後
    });
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 分断中の状態を確認
    const g1Result = await group1Clients[0].query("MATCH (n:PartitionTest {id: 'shared'}) RETURN n.value as value, n.lastGroup as lastGroup");
    const g2Result = await group2Clients[0].query("MATCH (n:PartitionTest {id: 'shared'}) RETURN n.value as value, n.lastGroup as lastGroup");
    
    assertEquals(g1Result[0].value, 100, "Group 1 should see its own update");
    assertEquals(g2Result[0].value, 200, "Group 2 should see its own update");
    
    // ネットワーク再結合
    console.log('🔗 Healing network partition...');
    await group1Clients[0].healPartition();
    await group2Clients[0].healPartition();
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 再結合後、すべてのクライアントが同じ状態を見るはず（Last-Write-Wins）
    console.log('🔍 Verifying convergence after healing...');
    const allClients = [...group1Clients, ...group2Clients];
    
    for (let i = 0; i < allClients.length; i++) {
      const result = await allClients[i].query("MATCH (n:PartitionTest {id: 'shared'}) RETURN n.value as value, n.lastGroup as lastGroup");
      assertEquals(result[0].value, 200, `Client ${i} should see converged value 200`);
      assertEquals(result[0].lastGroup, 'group2', `Client ${i} should see group2 as last updater`);
    }
    
    // クリーンアップ
    for (const client of allClients) {
      // クリーンアップはafterEachで実行
    }
  });

  it("should handle multi-step transactions atomically", async () => {
    console.log('\n🔴 TDD Red: Testing atomic multi-step transactions');
    
    const client = await createCausalSyncClient({
      clientId: 'transaction-client',
      dbPath: ':memory:',
      wsUrl: 'ws://localhost:8083'
    });
    allClients.push(client);
    
    // 初期アカウントを作成
    await client.executeOperation({
      id: 'create-accounts',
      dependsOn: [],
      type: 'CREATE',
      payload: {
        cypherQuery: `
          CREATE (a:Account {id: 'alice', balance: 1000})
          CREATE (b:Account {id: 'bob', balance: 500})
        `
      },
      clientId: client.id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // トランザクション: AliceからBobへ300送金
    const transferAmount = 300;
    const transactionId = 'transfer-001';
    
    await client.executeTransaction({
      id: transactionId,
      operations: [
        {
          id: `${transactionId}-debit`,
          type: 'UPDATE',
          payload: {
            cypherQuery: `MATCH (a:Account {id: 'alice'}) SET a.balance = a.balance - ${transferAmount}`
          }
        },
        {
          id: `${transactionId}-credit`,
          type: 'UPDATE',
          payload: {
            cypherQuery: `MATCH (b:Account {id: 'bob'}) SET b.balance = b.balance + ${transferAmount}`
          }
        }
      ],
      clientId: client.id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 両方の操作が適用されたことを確認
    const aliceResult = await client.query("MATCH (a:Account {id: 'alice'}) RETURN a.balance as balance");
    const bobResult = await client.query("MATCH (b:Account {id: 'bob'}) RETURN b.balance as balance");
    
    assertEquals(aliceResult[0].balance, 700, "Alice should have 700 after transfer");
    assertEquals(bobResult[0].balance, 800, "Bob should have 800 after transfer");
    
    // 総額が保持されていることを確認
    const totalBalance = aliceResult[0].balance + bobResult[0].balance;
    assertEquals(totalBalance, 1500, "Total balance should remain constant");
    
    // 失敗するトランザクションのテスト（残高不足）
    await client.executeTransaction({
      id: 'transfer-002-fail',
      operations: [
        {
          id: 'transfer-002-debit',
          type: 'UPDATE',
          payload: {
            cypherQuery: `MATCH (a:Account {id: 'alice'}) SET a.balance = a.balance - 1000`
          },
          constraint: {
            type: 'minimum_balance',
            value: 0
          }
        },
        {
          id: 'transfer-002-credit',
          type: 'UPDATE',
          payload: {
            cypherQuery: `MATCH (b:Account {id: 'bob'}) SET b.balance = b.balance + 1000`
          }
        }
      ],
      clientId: client.id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // トランザクションが失敗し、残高が変わっていないことを確認
    const aliceResultAfterFail = await client.query("MATCH (a:Account {id: 'alice'}) RETURN a.balance as balance");
    const bobResultAfterFail = await client.query("MATCH (b:Account {id: 'bob'}) RETURN b.balance as balance");
    
    assertEquals(aliceResultAfterFail[0].balance, 700, "Alice balance should not change after failed transaction");
    assertEquals(bobResultAfterFail[0].balance, 800, "Bob balance should not change after failed transaction");
    
    // クリーンアップはafterEachで実行
  });
});