// Test circular dependency detection
import { createCausalSyncClient, disconnect } from './causal-sync-client.ts';

console.log('Testing circular dependency detection...');

try {
  const client = await createCausalSyncClient({
    clientId: 'circular-test',
    dbPath: ':memory:',
    wsUrl: 'ws://localhost:8083'
  });
  
  console.log('Client connected');
  
  // Create circular dependencies: A → B → C → A
  await client.executeOperation({
    id: 'op-A',
    dependsOn: ['op-C'], // Circular!
    type: 'CREATE',
    payload: { cypherQuery: "CREATE (n:Circular {id: 'A'})" },
    clientId: client.id,
    timestamp: Date.now()
  });
  
  await client.executeOperation({
    id: 'op-B',
    dependsOn: ['op-A'],
    type: 'CREATE',
    payload: { cypherQuery: "CREATE (n:Circular {id: 'B'})" },
    clientId: client.id,
    timestamp: Date.now() + 1
  });
  
  await client.executeOperation({
    id: 'op-C',
    dependsOn: ['op-B'],
    type: 'CREATE',
    payload: { cypherQuery: "CREATE (n:Circular {id: 'C'})" },
    clientId: client.id,
    timestamp: Date.now() + 2
  });
  
  console.log('Operations sent');
  
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Check circular dependencies
  const circular = await client.getCircularDependencies();
  console.log('Circular dependencies detected:', circular);
  
  // Check that no operations were applied
  const result = await client.query("MATCH (n:Circular) RETURN count(n) as count");
  console.log('Nodes created:', result[0]?.count || 0);
  
  await disconnect(client);
  console.log('Test completed');
  
} catch (error) {
  console.error('Test failed:', error);
}