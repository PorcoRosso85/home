import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createKuzuSyncClient, disconnect } from './kuzu-sync-client.ts';
import type { KuzuSyncClient } from './kuzu-sync-client.ts';

async function test5Clients() {
  console.log('🔴 TDD Red Phase: Testing 5 clients with complex operations');
  
  const clientCount = 5;
  const clients: KuzuSyncClient[] = [];
  
  // 5つのクライアントを初期化
  for (let i = 0; i < clientCount; i++) {
    const client = await createKuzuSyncClient({
      clientId: `complex-client-${i}`,
      dbPath: ':memory:',
      wsUrl: 'ws://localhost:8081'
    });
    clients.push(client);
  }
  
  console.log('✅ All 5 clients connected');
  
  // Step 1: Client0がグラフ構造を作成
  console.log('\n📊 Client 0 creating graph structure...');
  await clients[0].executeAndBroadcast({
    id: crypto.randomUUID(),
    template: 'CREATE_GRAPH',
    params: {
      cypherQuery: `
        CREATE (alice:Person {id: 'alice', name: 'Alice', age: 30})
        CREATE (bob:Person {id: 'bob', name: 'Bob', age: 25})
        CREATE (charlie:Person {id: 'charlie', name: 'Charlie', age: 35})
        CREATE (dave:Person {id: 'dave', name: 'Dave', age: 28})
        CREATE (eve:Person {id: 'eve', name: 'Eve', age: 32})
      `
    },
    clientId: clients[0].id,
    timestamp: Date.now()
  });
  
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Step 2: 各クライアントが異なるリレーションシップを追加
  console.log('\n🔗 Each client adding relationships...');
  const relationships = [
    { from: 'alice', to: 'bob', type: 'KNOWS' },
    { from: 'bob', to: 'charlie', type: 'WORKS_WITH' },
    { from: 'charlie', to: 'dave', type: 'MANAGES' },
    { from: 'dave', to: 'eve', type: 'COLLABORATES_WITH' },
    { from: 'eve', to: 'alice', type: 'FRIENDS_WITH' }
  ];
  
  for (let i = 0; i < clientCount; i++) {
    const rel = relationships[i];
    await clients[i].executeAndBroadcast({
      id: crypto.randomUUID(),
      template: 'CREATE_RELATIONSHIP',
      params: {
        cypherQuery: `
          MATCH (a:Person {id: '${rel.from}'})
          MATCH (b:Person {id: '${rel.to}'})
          CREATE (a)-[:${rel.type}]->(b)
        `
      },
      clientId: clients[i].id,
      timestamp: Date.now()
    });
  }
  
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Step 3: 全クライアントで複雑なクエリを実行
  console.log('\n🔍 Verifying complex queries across all clients...');
  
  // クエリ1: 全ての人物をカウント
  for (let i = 0; i < clientCount; i++) {
    const result = await clients[i].query(`
      MATCH (p:Person)
      RETURN count(p) as totalPeople
    `);
    
    console.log(`Client ${i} result:`, result);
    assertEquals(result[0].totalPeople, 5, `Client ${i} should see 5 people`);
    console.log(`✅ Client ${i}: ${result[0].totalPeople} people found`);
  }
  
  // クエリ2: 特定のパスを検証
  for (let i = 0; i < clientCount; i++) {
    const result = await clients[i].query(`
      MATCH (alice:Person {id: 'alice'})-[:KNOWS]->(bob:Person {id: 'bob'})
      RETURN alice.name as alice, bob.name as bob
    `);
    
    assertExists(result[0], `Client ${i} should find Alice->Bob relationship`);
    assertEquals(result[0].alice, 'Alice');
    assertEquals(result[0].bob, 'Bob');
  }
  
  // Step 4: 並行更新テスト
  console.log('\n📝 Testing concurrent updates...');
  const updatePromises = [];
  
  for (let i = 0; i < clientCount; i++) {
    updatePromises.push(
      clients[i].executeAndBroadcast({
        id: crypto.randomUUID(),
        template: 'UPDATE_AGE',
        params: {
          cypherQuery: `
            MATCH (p:Person {id: 'alice'})
            SET p.age = p.age + 1
          `
        },
        clientId: clients[i].id,
        timestamp: Date.now()
      })
    );
  }
  
  await Promise.all(updatePromises);
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 最終状態の確認
  console.log('\n🏁 Verifying final state...');
  for (let i = 0; i < clientCount; i++) {
    const result = await clients[i].query(`
      MATCH (p:Person {id: 'alice'})
      RETURN p.age as age
    `);
    
    // 5回のインクリメントで35になるはず
    assertEquals(result[0].age, 35, `Client ${i} should see Alice's age as 35`);
    console.log(`✅ Client ${i}: Alice's age = ${result[0].age}`);
  }
  
  // クリーンアップ
  for (const client of clients) {
    await disconnect(client);
  }
  
  console.log('\n✅ Five clients complex operations test completed!');
}

test5Clients().catch(console.error);