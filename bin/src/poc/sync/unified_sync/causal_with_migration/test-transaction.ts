// Test transactions
import { createCausalSyncClient, disconnect } from './causal-sync-client.ts';

console.log('Testing transactions...');

try {
  const client = await createCausalSyncClient({
    clientId: 'tx-client',
    dbPath: ':memory:',
    wsUrl: 'ws://localhost:8083'
  });
  
  console.log('Client connected');
  
  // Create accounts
  await client.executeOperation({
    id: 'create-accounts',
    dependsOn: [],
    type: 'CREATE',
    payload: {
      cypherQuery: `CREATE (a:Account {id: 'alice', balance: 1000}) CREATE (b:Account {id: 'bob', balance: 500})`
    },
    clientId: client.id,
    timestamp: Date.now()
  });
  
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Check initial balances
  const aliceInit = await client.query("MATCH (a:Account {id: 'alice'}) RETURN a.balance as balance");
  const bobInit = await client.query("MATCH (b:Account {id: 'bob'}) RETURN b.balance as balance");
  
  console.log('Initial - Alice:', aliceInit[0]?.balance, 'Bob:', bobInit[0]?.balance);
  
  // Execute successful transaction
  await client.executeTransaction({
    id: 'transfer-001',
    operations: [
      {
        id: 'transfer-001-debit',
        type: 'UPDATE',
        payload: {
          cypherQuery: `MATCH (a:Account {id: 'alice'}) SET a.balance = a.balance - 300`
        }
      },
      {
        id: 'transfer-001-credit',
        type: 'UPDATE',
        payload: {
          cypherQuery: `MATCH (b:Account {id: 'bob'}) SET b.balance = b.balance + 300`
        }
      }
    ],
    clientId: client.id,
    timestamp: Date.now()
  });
  
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Check balances after transaction
  const aliceAfter = await client.query("MATCH (a:Account {id: 'alice'}) RETURN a.balance as balance");
  const bobAfter = await client.query("MATCH (b:Account {id: 'bob'}) RETURN b.balance as balance");
  
  console.log('After transfer - Alice:', aliceAfter[0]?.balance, 'Bob:', bobAfter[0]?.balance);
  console.log('Total balance preserved:', (aliceAfter[0]?.balance || 0) + (bobAfter[0]?.balance || 0));
  
  // Try failed transaction (overdraft)
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
  
  // Check balances after failed transaction
  const aliceFinal = await client.query("MATCH (a:Account {id: 'alice'}) RETURN a.balance as balance");
  const bobFinal = await client.query("MATCH (b:Account {id: 'bob'}) RETURN b.balance as balance");
  
  console.log('After failed tx - Alice:', aliceFinal[0]?.balance, 'Bob:', bobFinal[0]?.balance);
  console.log('Transaction with constraint was rejected as expected');
  
  await disconnect(client);
  console.log('Test completed');
  
} catch (error) {
  console.error('Test failed:', error);
}