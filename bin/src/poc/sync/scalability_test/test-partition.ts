// Test network partition
import { createCausalSyncClient, disconnect } from './causal-sync-client.ts';

console.log('Testing network partition...');

try {
  // Create two groups of clients
  const group1 = await createCausalSyncClient({
    clientId: 'g1-client',
    dbPath: ':memory:',
    wsUrl: 'ws://localhost:8083'
  });
  
  const group2 = await createCausalSyncClient({
    clientId: 'g2-client',
    dbPath: ':memory:',
    wsUrl: 'ws://localhost:8083'
  });
  
  console.log('Clients connected');
  
  // Create initial state
  await group1.executeOperation({
    id: 'init',
    dependsOn: [],
    type: 'CREATE',
    payload: {
      cypherQuery: "CREATE (n:Shared {id: 'data', value: 0})"
    },
    clientId: group1.id,
    timestamp: Date.now()
  });
  
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Simulate partition
  console.log('Simulating network partition...');
  await group1.simulatePartition(['g1-client']);
  await group2.simulatePartition(['g2-client']);
  
  // Each group makes updates
  await group1.executeOperation({
    id: 'g1-update',
    dependsOn: ['init'],
    type: 'UPDATE',
    payload: {
      cypherQuery: "MATCH (n:Shared {id: 'data'}) SET n.value = 100"
    },
    clientId: group1.id,
    timestamp: Date.now() + 1000
  });
  
  await group2.executeOperation({
    id: 'g2-update',
    dependsOn: ['init'],
    type: 'UPDATE',
    payload: {
      cypherQuery: "MATCH (n:Shared {id: 'data'}) SET n.value = 200"
    },
    clientId: group2.id,
    timestamp: Date.now() + 2000
  });
  
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Check values during partition
  const g1Result = await group1.query("MATCH (n:Shared {id: 'data'}) RETURN n.value as value");
  const g2Result = await group2.query("MATCH (n:Shared {id: 'data'}) RETURN n.value as value");
  
  console.log('During partition - Group 1 sees:', g1Result[0]?.value);
  console.log('During partition - Group 2 sees:', g2Result[0]?.value);
  
  // Heal partition
  console.log('Healing partition...');
  await group1.healPartition();
  await group2.healPartition();
  
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Check converged values
  const g1Final = await group1.query("MATCH (n:Shared {id: 'data'}) RETURN n.value as value");
  const g2Final = await group2.query("MATCH (n:Shared {id: 'data'}) RETURN n.value as value");
  
  console.log('After healing - Group 1 sees:', g1Final[0]?.value);
  console.log('After healing - Group 2 sees:', g2Final[0]?.value);
  
  await disconnect(group1);
  await disconnect(group2);
  console.log('Test completed');
  
} catch (error) {
  console.error('Test failed:', error);
}