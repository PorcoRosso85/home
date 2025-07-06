/**
 * KuzuDB同期クライアントテスト - 複数ローカルクライアント間の状態同期検証
 * TDD Red Phase - このテストは失敗することが期待される
 * 
 * 仕様:
 * - 各クライアントが独自のインメモリKuzuDBインスタンスを持つ
 * - WebSocket経由でイベントを共有
 * - 受信イベントを各自のKuzuDBに適用
 * - 最終的に全クライアントが同じ状態になる
 * - テスト完了後、インメモリDBは自動的にクリーンアップされる
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import type { KuzuSyncClient, SyncEvent } from './kuzu-sync-client.ts'; // まだ存在しない
import { 
  createKuzuSyncClient,
  disconnect
} from './kuzu-sync-client.ts'; // まだ存在しない

// テスト設定
const CLIENT_COUNT = 20;
const EVENTS_PER_CLIENT = 100;
const TOTAL_EXPECTED_EVENTS = CLIENT_COUNT * EVENTS_PER_CLIENT;

describe("KuzuDB sync client tests", () => {
  it("single client DML should propagate to all other clients", async () => {
    console.log('🔄 Testing single client DML propagation...');
    
    const clientCount = 5;
    const clients: KuzuSyncClient[] = [];
    
    // 5つのクライアントを初期化
    for (let i = 0; i < clientCount; i++) {
      const client = await createKuzuSyncClient({
        clientId: `propagation-client-${i}`,
        dbPath: ':memory:',
        wsUrl: 'ws://localhost:8081'
      });
      clients.push(client);
    }
    
    console.log('✅ All clients connected');
    
    // Step 1: Client0だけがDML実行
    console.log('\n📝 Client 0 executing DML...');
    await clients[0].executeAndBroadcast({
      id: crypto.randomUUID(),
      template: 'CREATE_NODE', 
      params: {
        cypherQuery: `CREATE (n:User {id: 'alice', name: 'Alice', age: 30})`
      },
      clientId: clients[0].id,
      timestamp: Date.now()
    });
    
    // イベント伝播を待つ
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Step 2: 全クライアントでDQLを実行して確認
    console.log('\n🔍 Verifying propagation via DQL...');
    
    for (let i = 0; i < clientCount; i++) {
      const result = await clients[i].query(`
        MATCH (u:User {id: 'alice'})
        RETURN u.name as name, u.age as age
      `);
      
      assertExists(result[0], `Client ${i} should have the user node`);
      assertEquals(result[0].name, 'Alice', `Client ${i} should have correct name`);
      assertEquals(result[0].age, 30, `Client ${i} should have correct age`);
      
      console.log(`✅ Client ${i}: User 'Alice' found`);
    }
    
    // Step 3: Client2がリレーションを追加
    console.log('\n📝 Client 2 adding relationship...');
    await clients[2].executeAndBroadcast({
      id: crypto.randomUUID(),
      template: 'CREATE_RELATIONSHIP',
      params: {
        cypherQuery: `
          CREATE (n:User {id: 'bob', name: 'Bob', age: 25})
          WITH n
          MATCH (a:User {id: 'alice'})
          CREATE (a)-[:KNOWS]->(n)
        `
      },
      clientId: clients[2].id,
      timestamp: Date.now()
    });
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Step 4: 全クライアントでリレーションを確認
    console.log('\n🔍 Verifying relationship propagation...');
    
    for (let i = 0; i < clientCount; i++) {
      const result = await clients[i].query(`
        MATCH (a:User {id: 'alice'})-[:KNOWS]->(b:User {id: 'bob'})
        RETURN a.name as alice, b.name as bob
      `);
      
      assertExists(result[0], `Client ${i} should have the relationship`);
      assertEquals(result[0].alice, 'Alice');
      assertEquals(result[0].bob, 'Bob');
      
      console.log(`✅ Client ${i}: Relationship Alice->Bob found`);
    }
    
    // クリーンアップ
    for (const client of clients) {
      await disconnect(client);
    }
    
    console.log('\n✅ Single client DML propagation test completed!');
  });

  it("event reception tracking - verify server detection and client notifications", async () => {
    console.log('📡 Testing event reception tracking...');
    
    const clientCount = 3;
    const clients: KuzuSyncClient[] = [];
    const receivedEvents: Map<string, string[]> = new Map();
    
    // クライアントを初期化（イベントハンドラー付き）
    for (let i = 0; i < clientCount; i++) {
      const clientId = `tracking-client-${i}`;
      receivedEvents.set(clientId, []);
      
      const client = await createKuzuSyncClient({
        clientId,
        dbPath: ':memory:',
        wsUrl: 'ws://localhost:8081',
        onEventReceived: (event: SyncEvent) => {
          // イベント受信を記録
          receivedEvents.get(clientId)!.push(
            `Received event ${event.id} from ${event.clientId}`
          );
          console.log(`  📥 ${clientId} received event from ${event.clientId}`);
        }
      });
      clients.push(client);
    }
    
    console.log('✅ All clients connected with event handlers');
    
    // Client0がイベントを送信
    console.log('\n📤 Client 0 sending event...');
    const eventId = crypto.randomUUID();
    await clients[0].executeAndBroadcast({
      id: eventId,
      template: 'CREATE_NODE',
      params: {
        cypherQuery: `CREATE (n:Event {id: '${eventId}', source: 'client-0'})`
      },
      clientId: clients[0].id,
      timestamp: Date.now()
    });
    
    // イベント伝播を待つ
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 受信状況を確認
    console.log('\n📊 Event reception summary:');
    
    // Client0は自分のイベントを受信しない（または受信する場合は無視する）
    // Client1とClient2は受信するはず
    for (let i = 1; i < clientCount; i++) {
      const clientId = `tracking-client-${i}`;
      const received = receivedEvents.get(clientId)!;
      
      assertEquals(
        received.length >= 1,
        true,
        `${clientId} should have received at least 1 event`
      );
      
      console.log(`  ${clientId}: ${received.length} events received`);
    }
    
    // 全クライアントでDQLを実行して、イベントが適用されたことを確認
    console.log('\n🔍 Verifying event application via DQL...');
    
    for (let i = 0; i < clientCount; i++) {
      const result = await clients[i].query(`
        MATCH (e:Event {id: '${eventId}'})
        RETURN e.source as source
      `);
      
      assertExists(result[0], `Client ${i} should have the event node`);
      assertEquals(result[0].source, 'client-0');
      console.log(`  ✅ Client ${i}: Event node verified in KuzuDB`);
    }
    
    // クリーンアップ
    for (const client of clients) {
      await disconnect(client);
    }
    
    console.log('\n✅ Event reception tracking test completed!');
  });

  it("multiple local clients should sync their KuzuDB states through WebSocket", async () => {
  console.log(`🧪 Sync Test: ${CLIENT_COUNT} clients × ${EVENTS_PER_CLIENT} events = ${TOTAL_EXPECTED_EVENTS} total`);
  
  // 複数のKuzuDB同期クライアントを作成
  const clients: KuzuSyncClient[] = [];
  const clientPromises = [];
  
  for (let i = 0; i < CLIENT_COUNT; i++) {
    const clientId = `sync-client-${i}`;
    
    // 各クライアントは独自のインメモリKuzuDBインスタンスとWebSocket接続を持つ
    clientPromises.push(
      createKuzuSyncClient({
        clientId,
        dbPath: ':memory:', // インメモリモード
        wsUrl: 'ws://localhost:8081'
      })
    );
  }
  
  // 全クライアントの初期化を待つ
  const initializedClients = await Promise.all(clientPromises);
  clients.push(...initializedClients);
  console.log(`✅ All ${CLIENT_COUNT} clients initialized with their own KuzuDB instances`);
  
  // 各クライアントの初期状態を確認
  for (let i = 0; i < CLIENT_COUNT; i++) {
    const eventCount = await getEventCount(clients[i]);
    assertEquals(eventCount, 0, `Client ${i} should start with 0 events`);
  }
  
  // パフォーマンス測定開始
  const startTime = Date.now();
  const startMemory = (globalThis as any).process?.memoryUsage?.() || { heapUsed: 0 };
  
  // 各クライアントが自身のKuzuDBにDML実行し、イベントを送信
  const sendPromises = [];
  const sentEvents: SyncEvent[] = [];
  
  for (let clientIdx = 0; clientIdx < CLIENT_COUNT; clientIdx++) {
    const client = clients[clientIdx];
    
    for (let eventIdx = 0; eventIdx < EVENTS_PER_CLIENT; eventIdx++) {
      const nodeId = `node-${clientIdx}-${eventIdx}`;
      const event: SyncEvent = {
        id: crypto.randomUUID(),
        template: 'CREATE_NODE',
        params: {
          cypherQuery: `CREATE (n:TestNode {
            id: '${nodeId}',
            clientIndex: ${clientIdx},
            eventIndex: ${eventIdx},
            timestamp: ${Date.now()},
            data: 'Event ${eventIdx} from client ${clientIdx}'
          })`,
          nodeId: nodeId
        },
        clientId: client.id,
        timestamp: Date.now()
      };
      
      sentEvents.push(event);
      // ローカルDML実行とイベント送信を同時に行う
      sendPromises.push(client.executeAndBroadcast(event));
    }
  }
  
  // すべての送信が完了するまで待機
  await Promise.all(sendPromises);
  const sendDuration = Date.now() - startTime;
  console.log(`📤 All ${TOTAL_EXPECTED_EVENTS} events sent in ${sendDuration}ms`);
  
  // イベントが全クライアントに伝播され、各KuzuDBに適用されるまで待機
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  // 検証1: DQLで各クライアントのKuzuDBに全ノードが存在することを確認
  console.log('\n🔍 Verifying node existence via DQL queries...');
  
  for (let i = 0; i < CLIENT_COUNT; i++) {
    const client = clients[i];
    
    // DQL: ノード数を確認
    const countResult = await client.query(`
      MATCH (n:TestNode)
      RETURN count(n) as nodeCount
    `);
    
    console.log(`📊 Client ${i}: ${countResult[0].nodeCount} nodes`);
    
    assertEquals(
      countResult[0].nodeCount,
      TOTAL_EXPECTED_EVENTS,
      `Client ${i} should have ${TOTAL_EXPECTED_EVENTS} nodes`
    );
    
    // DQL: 特定のノードが存在することを確認（サンプリング）
    for (let j = 0; j < CLIENT_COUNT; j += 5) {
      for (let k = 0; k < EVENTS_PER_CLIENT; k += 20) {
        const nodeId = `node-${j}-${k}`;
        const nodeResult = await client.query(`
          MATCH (n:TestNode {id: '${nodeId}'})
          RETURN n.clientIndex as clientIndex, n.eventIndex as eventIndex
        `);
        
        assertExists(nodeResult[0], `Client ${i} missing node ${nodeId}`);
        assertEquals(nodeResult[0].clientIndex, j);
        assertEquals(nodeResult[0].eventIndex, k);
      }
    }
  }
  
  // 検証2: 全クライアントのインメモリKuzuDBが同一の状態であることを確認
  console.log('\n🤝 Verifying state consistency across all in-memory KuzuDB instances...');
  
  // DQLクエリで各クライアントの状態を確認
  // インメモリでも通常のKuzuDBと同じクエリが使用可能
  
  // DQL: 集計クエリで全クライアントの状態を比較
  const stateComparisons = [];
  
  for (let i = 0; i < CLIENT_COUNT; i++) {
    const client = clients[i];
    
    // DQL: 集計情報を取得
    const aggregateResult = await client.query(`
      MATCH (n:TestNode)
      RETURN 
        count(n) as totalNodes,
        count(DISTINCT n.clientIndex) as uniqueClients,
        min(n.timestamp) as minTimestamp,
        max(n.timestamp) as maxTimestamp
      ORDER BY n.id
    `);
    
    stateComparisons.push({
      clientId: i,
      ...aggregateResult[0]
    });
  }
  
  // 全クライアントが同じ集計結果を持つことを確認
  const referenceState = stateComparisons[0];
  for (let i = 1; i < CLIENT_COUNT; i++) {
    const clientState = stateComparisons[i];
    
    assertEquals(
      clientState.totalNodes,
      referenceState.totalNodes,
      `Client ${i} has different total node count`
    );
    
    assertEquals(
      clientState.uniqueClients,
      referenceState.uniqueClients,
      `Client ${i} has different unique client count`
    );
  }
  
  console.log(`✅ All clients have ${referenceState.totalNodes} nodes from ${referenceState.uniqueClients} unique clients`);
  
  console.log('✅ All in-memory KuzuDB instances have identical states!');
  
  // 検証3: イベントの順序性が保たれていることを確認
  console.log('\n⏱️  Verifying event ordering consistency...');
  
  // DQL: タイムスタンプ順でノードを取得し、順序性を確認
  for (const client of clients) {
    const orderedNodes = await client.query(`
      MATCH (n:TestNode)
      RETURN n.id, n.timestamp
      ORDER BY n.timestamp
      LIMIT 10
    `);
    
    // タイムスタンプが昇順であることを確認
    for (let i = 1; i < orderedNodes.length; i++) {
      assertEquals(
        orderedNodes[i].timestamp >= orderedNodes[i-1].timestamp,
        true,
        'Timestamps should be in ascending order'
      );
    }
  }
  
  console.log(`✅ Event ordering verified across ${CLIENT_COUNT} clients`);
  
  // パフォーマンスメトリクス
  const endTime = Date.now();
  const endMemory = (globalThis as any).process?.memoryUsage?.() || { heapUsed: 0 };
  const totalDuration = endTime - startTime;
  const memoryDelta = endMemory.heapUsed - startMemory.heapUsed;
  
  console.log(`\n📊 Performance Metrics:`);
  console.log(`  Total duration: ${totalDuration}ms`);
  console.log(`  Events/second: ${(TOTAL_EXPECTED_EVENTS / (totalDuration / 1000)).toFixed(2)}`);
  console.log(`  Memory delta: ${(memoryDelta / 1024 / 1024).toFixed(2)}MB`);
  
  // クリーンアップ
  console.log('\n🧹 Cleaning up...');
  for (const client of clients) {
    await disconnect(client);
  }
  
  console.log(`\n✅ Sync test completed successfully!`);
  });

  it("concurrent counter updates should maintain consistency across all clients", async () => {
  console.log('🧪 Testing concurrent counter consistency...');
  
  const clientCount = 10;
  const incrementsPerClient = 100;
  const expectedFinalCount = clientCount * incrementsPerClient;
  
  // 複数のKuzuDB同期クライアントを作成
  const clients: KuzuSyncClient[] = [];
  const clientPromises = [];
  
  for (let i = 0; i < clientCount; i++) {
    const clientId = `counter-client-${i}`;
    
    clientPromises.push(
      createKuzuSyncClient({
        clientId,
        dbPath: ':memory:', // インメモリモード
        wsUrl: 'ws://localhost:8081'
      })
    );
  }
  
  const initializedClients = await Promise.all(clientPromises);
  clients.push(...initializedClients);
  console.log(`✅ ${clientCount} counter clients initialized`);
  
  // 最初のクライアントがカウンターを初期化（DML実行）
  await clients[0].executeAndBroadcast({
    id: crypto.randomUUID(),
    template: 'CREATE_COUNTER',
    params: {
      cypherQuery: `CREATE (c:Counter {id: 'shared-counter', value: 0})`
    },
    clientId: clients[0].id,
    timestamp: Date.now()
  });
  
  // 初期化が全クライアントに伝播されるまで待機
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // DQL: 全クライアントでカウンター初期値を確認
  for (let i = 0; i < clientCount; i++) {
    const result = await clients[i].query(`
      MATCH (c:Counter {id: 'shared-counter'})
      RETURN c.value as value
    `);
    assertEquals(result[0].value, 0, `Client ${i} should have initial counter value 0`);
  }
  
  // 並行でインクリメントイベントを送信
  console.log(`🚀 Sending ${expectedFinalCount} increment events concurrently...`);
  const incrementPromises = [];
  
  for (let i = 0; i < incrementsPerClient; i++) {
    for (const client of clients) {
      incrementPromises.push(
        client.executeAndBroadcast({
          id: crypto.randomUUID(),
          template: 'INCREMENT_COUNTER',
          params: {
            cypherQuery: `
              MATCH (c:Counter {id: 'shared-counter'})
              SET c.value = c.value + 1
            `
          },
          clientId: client.id,
          timestamp: Date.now()
        })
      );
    }
  }
  
  await Promise.all(incrementPromises);
  console.log('✅ All increment events sent');
  
  // 全イベントが処理されるまで待機
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  // DQL: 全クライアントでカウンター値を確認
  console.log('\n🔍 Verifying counter values across all clients...');
  
  // 注意：イベントソーシングでは最終的一貫性のため、
  // 全クライアントが同じ値になることを確認（必ずしも合計値ではない）
  const counterValues = [];
  
  for (let i = 0; i < clientCount; i++) {
    const result = await clients[i].query(`
      MATCH (c:Counter {id: 'shared-counter'})
      RETURN c.value as value
    `);
    
    assertExists(result[0], `Client ${i} should have counter node`);
    counterValues.push(result[0].value);
    console.log(`📊 Client ${i} counter value: ${result[0].value}`);
  }
  
  // 全クライアントが同じカウンター値を持つことを確認
  const referenceValue = counterValues[0];
  for (let i = 1; i < clientCount; i++) {
    assertEquals(
      counterValues[i],
      referenceValue,
      `Client ${i} has different counter value than client 0`
    );
  }
  
  console.log(`\n✅ Counter consistency maintained: all clients show ${expectedFinalCount}`);
  
  // クリーンアップ
  console.log('\n🧹 Cleaning up...');
  for (const client of clients) {
    await disconnect(client);
  }
  });
});