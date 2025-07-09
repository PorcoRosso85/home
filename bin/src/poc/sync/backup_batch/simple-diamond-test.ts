// Simple test for diamond dependency
import { createCausalSyncClient, disconnect } from './causal-sync-client.ts';

console.log('Starting simple diamond test...');

try {
  const client = await createCausalSyncClient({
    clientId: 'diamond-test',
    dbPath: ':memory:',
    wsUrl: 'ws://localhost:8083'
  });
  
  console.log('Client connected');
  
  // Create operations in order
  await client.executeOperation({
    id: 'op-A',
    dependsOn: [],
    type: 'CREATE',
    payload: {
      cypherQuery: "CREATE (n:Diamond {id: 'node', step: 'A'})"
    },
    clientId: client.id,
    timestamp: Date.now()
  });
  
  console.log('Operation A executed');
  
  await new Promise(resolve => setTimeout(resolve, 100));
  
  await client.executeOperation({
    id: 'op-B',
    dependsOn: ['op-A'],
    type: 'UPDATE',
    payload: {
      cypherQuery: "MATCH (n:Diamond {id: 'node'}) SET n.step = 'B'"
    },
    clientId: client.id,
    timestamp: Date.now()
  });
  
  console.log('Operation B executed');
  
  await client.executeOperation({
    id: 'op-C',
    dependsOn: ['op-A'],
    type: 'UPDATE',
    payload: {
      cypherQuery: "MATCH (n:Diamond {id: 'node'}) SET n.step = 'C'"
    },
    clientId: client.id,
    timestamp: Date.now()
  });
  
  console.log('Operation C executed');
  
  await client.executeOperation({
    id: 'op-D',
    dependsOn: ['op-B', 'op-C'],
    type: 'UPDATE',
    payload: {
      cypherQuery: "MATCH (n:Diamond {id: 'node'}) SET n.step = 'D'"
    },
    clientId: client.id,
    timestamp: Date.now()
  });
  
  console.log('Operation D executed');
  
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const result = await client.query("MATCH (n:Diamond {id: 'node'}) RETURN n.step as step");
  console.log('Query result:', result);
  
  const history = await client.getOperationHistory();
  console.log('Operation history:', history.map(op => op.id));
  
  await disconnect(client);
  console.log('Test completed successfully');
  
} catch (error) {
  console.error('Test failed:', error);
}