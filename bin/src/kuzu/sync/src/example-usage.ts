#!/usr/bin/env node --experimental-strip-types
/**
 * Example usage of the MinimalSyncClient
 * 
 * This demonstrates:
 * - Creating a sync client
 * - Connecting to a WebSocket server
 * - Creating nodes with properties
 * - Updating properties
 * - Handling offline/online scenarios
 * - Server reconciliation
 */

import { createSyncClient } from './sync-client.ts';

async function main() {
  console.log('KuzuDB Sync Client Example');
  console.log('==========================\n');

  // Configuration
  const config = {
    serverUrl: process.env.SYNC_SERVER_URL || 'ws://localhost:8080/sync',
    clientId: process.env.CLIENT_ID || `client-${Date.now()}`,
    databasePath: process.env.DB_PATH || './example-sync.db',
    reconnectInterval: 5000,
    heartbeatInterval: 30000
  };

  console.log('Configuration:');
  console.log(`- Server URL: ${config.serverUrl}`);
  console.log(`- Client ID: ${config.clientId}`);
  console.log(`- Database: ${config.databasePath}`);
  console.log('');

  let client;
  
  try {
    // Create and initialize the sync client
    console.log('Connecting to sync server...');
    client = await createSyncClient(config);
    console.log('Connected successfully!\n');

    // Example 1: Create a graph structure
    console.log('Creating graph structure...');
    
    // Create person nodes
    const alice = await client.createNode('Person', {
      name: 'Alice',
      age: 30,
      occupation: 'Software Engineer',
      city: 'New York'
    });
    console.log(`Created node: ${alice}`);

    const bob = await client.createNode('Person', {
      name: 'Bob',
      age: 28,
      occupation: 'Data Scientist',
      city: 'San Francisco'
    });
    console.log(`Created node: ${bob}`);

    const charlie = await client.createNode('Person', {
      name: 'Charlie',
      age: 35,
      occupation: 'Product Manager',
      city: 'Seattle'
    });
    console.log(`Created node: ${charlie}`);

    // Create company nodes
    const techCorp = await client.createNode('Company', {
      name: 'TechCorp',
      industry: 'Technology',
      founded: 2010,
      employees: 5000
    });
    console.log(`Created node: ${techCorp}`);

    const dataInc = await client.createNode('Company', {
      name: 'DataInc',
      industry: 'Analytics',
      founded: 2015,
      employees: 500
    });
    console.log(`Created node: ${dataInc}`);

    console.log('\nInitial sync status:');
    console.log(`- Connected: ${client.isReady()}`);
    console.log(`- Pending patches: ${client.getPendingPatchCount()}`);
    console.log(`- Server version: ${client.getServerVersion()}`);

    // Example 2: Update properties
    console.log('\nUpdating properties...');
    await client.setProperty('node', alice, 'skills', ['JavaScript', 'TypeScript', 'Python']);
    await client.setProperty('node', bob, 'skills', ['Python', 'R', 'SQL']);
    await client.setProperty('node', charlie, 'skills', ['Product Management', 'Agile', 'Analytics']);

    // Update company information
    await client.setProperty('node', techCorp, 'revenue', 1000000000);
    await client.setProperty('node', dataInc, 'revenue', 50000000);

    console.log('Properties updated');

    // Example 3: Simulate offline scenario
    console.log('\nSimulating offline scenario...');
    console.log('(In a real scenario, you would disconnect the network here)');
    
    // Create more changes while "offline"
    const david = await client.createNode('Person', {
      name: 'David',
      age: 26,
      occupation: 'Junior Developer',
      city: 'Austin'
    });
    
    await client.setProperty('node', david, 'mentor', alice);
    await client.setProperty('node', alice, 'mentees', [david]);

    console.log(`Created node while offline: ${david}`);
    console.log(`Pending patches: ${client.getPendingPatchCount()}`);

    // Wait for sync
    console.log('\nWaiting for synchronization...');
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Final status
    console.log('\nFinal sync status:');
    console.log(`- Connected: ${client.isReady()}`);
    console.log(`- Pending patches: ${client.getPendingPatchCount()}`);
    console.log(`- Server version: ${client.getServerVersion()}`);

    // Example 4: Conflict resolution scenario
    console.log('\nConflict resolution example:');
    console.log('(In a real multi-client scenario, conflicts would be resolved by the server)');
    
    // Update the same property multiple times
    await client.setProperty('node', alice, 'age', 31);
    await client.setProperty('node', alice, 'age', 32);
    console.log('Updated same property multiple times - server will reconcile');

  } catch (error) {
    console.error('Error:', error);
    console.log('\nNote: This example requires a WebSocket sync server to be running.');
    console.log('The sync client will attempt to reconnect automatically.');
  } finally {
    if (client) {
      console.log('\nClosing sync client...');
      await client.close();
      console.log('Client closed successfully.');
    }
  }
}

// Run the example
main().catch(console.error);