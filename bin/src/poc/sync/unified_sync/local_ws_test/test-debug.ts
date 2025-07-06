import { createKuzuSyncClient, disconnect } from './kuzu-sync-client.ts';

// デバッグテスト
async function testRelationshipQuery() {
  console.log('Starting debug test...');
  
  // 1つのクライアントを作成
  const client = await createKuzuSyncClient({
    clientId: 'debug-client',
    dbPath: ':memory:',
    wsUrl: 'ws://localhost:8081'
  });
  
  // Aliceを作成
  await client.executeAndBroadcast({
    id: '1',
    template: 'CREATE_NODE',
    params: {
      cypherQuery: `CREATE (n:User {id: 'alice', name: 'Alice', age: 30})`
    },
    clientId: client.id,
    timestamp: Date.now()
  });
  
  // Bobとリレーションシップを作成
  await client.executeAndBroadcast({
    id: '2',
    template: 'CREATE_RELATIONSHIP',
    params: {
      cypherQuery: `
        CREATE (n:User {id: 'bob', name: 'Bob', age: 25})
        WITH n
        MATCH (a:User {id: 'alice'})
        CREATE (a)-[:KNOWS]->(n)
      `
    },
    clientId: client.id,
    timestamp: Date.now()
  });
  
  // クエリを実行
  console.log('\nQuerying for Alice...');
  const aliceResult = await client.query(`
    MATCH (u:User {id: 'alice'})
    RETURN u.name as name, u.age as age
  `);
  console.log('Alice result:', aliceResult);
  
  console.log('\nQuerying for Bob...');
  const bobResult = await client.query(`
    MATCH (u:User {id: 'bob'})
    RETURN u.name as name, u.age as age
  `);
  console.log('Bob result:', bobResult);
  
  console.log('\nQuerying for relationship...');
  const relResult = await client.query(`
    MATCH (a:User {id: 'alice'})-[:KNOWS]->(b:User {id: 'bob'})
    RETURN a.name as alice, b.name as bob
  `);
  console.log('Relationship result:', relResult);
  
  await disconnect(client);
  console.log('\nTest completed');
}

// 実行
testRelationshipQuery().catch(console.error);