import { test, describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { MinimalSyncClient } from './sync-client.ts';
import { generateId } from './types/protocol.ts';
import { patchToCypher } from './patch-to-cypher.ts';

describe('Sync Client Standalone Tests', () => {
  it('should create a client instance without connecting', () => {
    const client = new MinimalSyncClient({
      serverUrl: 'ws://localhost:9999/sync',
      clientId: 'test-client-001',
      databasePath: ':memory:'
    });
    
    assert.ok(client, 'Client should be created');
    assert.equal(client.isReady(), false, 'Client should not be ready without connection');
    assert.equal(client.getPendingPatchCount(), 0, 'Should have no pending patches initially');
  });

  it('should generate proper IDs', () => {
    const nodeId = generateId('node');
    const edgeId = generateId('edge');
    const patchId = generateId('patch');
    
    assert.ok(nodeId.startsWith('n_'), 'Node ID should start with n_');
    assert.ok(edgeId.startsWith('e_'), 'Edge ID should start with e_');
    assert.ok(patchId.startsWith('p_'), 'Patch ID should start with p_');
  });

  it('should convert patches to Cypher queries', () => {
    const patch = {
      id: generateId('patch'),
      op: 'create_node' as const,
      nodeId: generateId('node'),
      timestamp: Date.now(),
      clientId: 'test-client',
      data: {
        label: 'Person',
        properties: {
          name: 'Alice',
          age: 30
        }
      }
    };
    
    const query = patchToCypher(patch);
    
    assert.ok(query.statement.includes('CREATE'), 'Query should contain CREATE');
    assert.ok(query.statement.includes('Person'), 'Query should contain label');
    assert.equal(query.parameters.name, 'Alice', 'Parameters should include name');
    assert.equal(query.parameters.age, 30, 'Parameters should include age');
  });

  it('should handle property patches', () => {
    const patch = {
      id: generateId('patch'),
      op: 'set_property' as const,
      targetType: 'node' as const,
      targetId: generateId('node'),
      propertyKey: 'status',
      propertyValue: 'active',
      timestamp: Date.now(),
      clientId: 'test-client'
    };
    
    const query = patchToCypher(patch);
    
    assert.ok(query.statement.includes('SET'), 'Query should contain SET');
    assert.ok(query.statement.includes('status'), 'Query should contain property key');
    assert.equal(query.parameters.value, 'active', 'Parameters should include value');
  });

  it('should validate label names', () => {
    const invalidPatch = {
      id: generateId('patch'),
      op: 'create_node' as const,
      nodeId: generateId('node'),
      timestamp: Date.now(),
      clientId: 'test-client',
      data: {
        label: 'Invalid-Label!', // Invalid characters
        properties: {}
      }
    };
    
    assert.throws(
      () => patchToCypher(invalidPatch),
      /Invalid label/,
      'Should throw error for invalid label'
    );
  });

  it('should validate property keys', () => {
    const invalidPatch = {
      id: generateId('patch'),
      op: 'set_property' as const,
      targetType: 'node' as const,
      targetId: generateId('node'),
      propertyKey: 'invalid-key!', // Invalid characters
      propertyValue: 'value',
      timestamp: Date.now(),
      clientId: 'test-client'
    };
    
    assert.throws(
      () => patchToCypher(invalidPatch),
      /Invalid property key/,
      'Should throw error for invalid property key'
    );
  });
});

// Run tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('Running standalone sync client tests...');
}