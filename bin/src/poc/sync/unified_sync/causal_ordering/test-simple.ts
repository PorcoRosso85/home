// Test simple causal ordering functionality
import { createCausalSyncClient, disconnect } from './causal-sync-client.ts';

console.log('Starting simple test...');

// Start server
const serverProcess = new Deno.Command("deno", {
  args: ["run", "--allow-net", "websocket-server.ts"],
  stdout: "piped",
  stderr: "piped",
});

const server = serverProcess.spawn();

// Wait for server to start
await new Promise(resolve => setTimeout(resolve, 1000));

try {
  // Create client
  const client = await createCausalSyncClient({
    clientId: 'test-client',
    dbPath: ':memory:',
    wsUrl: 'ws://localhost:8083'
  });

  console.log('Client created successfully');

  // Test basic operation
  await client.executeOperation({
    id: 'test-op',
    dependsOn: [],
    type: 'CREATE',
    payload: {
      cypherQuery: "CREATE (n:Test {id: 'test', value: 42})"
    },
    clientId: client.id,
    timestamp: Date.now()
  });

  console.log('Operation executed');

  await new Promise(resolve => setTimeout(resolve, 500));

  // Query result
  const result = await client.query("MATCH (n:Test {id: 'test'}) RETURN n.value as value");
  console.log('Query result:', result);

  // Test new APIs
  const circular = await client.getCircularDependencies();
  console.log('Circular dependencies:', circular);

  await disconnect(client);
  console.log('Test completed successfully');

} finally {
  // Kill server
  server.kill();
}