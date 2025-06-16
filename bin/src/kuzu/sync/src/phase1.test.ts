import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, rmSync, mkdirSync } from 'fs';
import { createSnapshotManager } from './snapshotManager.ts';
import { createDiffEngine } from './diffEngine.ts';
import { createMemoryManager } from './memoryManager.ts';
import type { GraphState, HistoryEntry } from './memoryManager.ts';

// Test setup
const testDir = './test-snapshots';

describe('Phase 1: Foundation Tests', () => {
  
  describe('Snapshot Manager', () => {
    test('should create and load snapshots', async () => {
      // Create test directory
      if (!existsSync(testDir)) mkdirSync(testDir, { recursive: true });
      
      const snapshotManager = createSnapshotManager(testDir);
      
      // Create mock database that simulates KuzuDB behavior
      const mockDb = {
        tables: [
          { name: 'Person', type: 'NODE' },
          { name: 'Knows', type: 'REL' }
        ],
        nodes: [
          { n: { id: 1, name: 'Alice' } },
          { n: { id: 2, name: 'Bob' } }
        ],
        execute: async (query: string) => {
          if (query === 'SHOW TABLES') {
            return mockDb.tables;
          }
          if (query === 'MATCH (n:Person) RETURN n') {
            return mockDb.nodes;
          }
          if (query === 'MATCH ()-[r:Knows]->() RETURN r') {
            return []; // No relationships for simplicity
          }
          if (query === 'MATCH (n) DETACH DELETE n') {
            mockDb.nodes = [];
            return [];
          }
          if (query.startsWith('CREATE')) {
            // Parse and add node back
            const match = query.match(/CREATE \(:Person \{id: (\d+), name: "([^"]+)"\}\)/);
            if (match) {
              mockDb.nodes.push({ n: { id: parseInt(match[1]), name: match[2] } });
            }
            return [];
          }
          return [];
        }
      };
      
      // Create snapshot
      const createResult = await snapshotManager.createSnapshot(mockDb, 1);
      
      // Debug output
      if ('code' in createResult) {
        console.error('Snapshot creation failed:', createResult);
      }
      
      // Verify snapshot creation
      assert.ok(!('code' in createResult), 'Should create snapshot successfully');
      assert.equal(createResult.version, 1);
      assert.ok(createResult.timestamp > 0);
      assert.ok(createResult.size > 0);
      assert.ok(existsSync(createResult.path));
      
      // Clear database
      await mockDb.execute('MATCH (n) DETACH DELETE n');
      
      // Verify data is cleared
      assert.equal(mockDb.nodes.length, 0, 'Database should be empty');
      
      // Load snapshot
      const loadResult = await snapshotManager.loadSnapshot(mockDb, createResult.id);
      assert.ok('success' in loadResult && loadResult.success, 'Should load snapshot successfully');
      
      // Verify data is restored
      assert.equal(mockDb.nodes.length, 2);
      
      // Get latest snapshot
      const latestResult = await snapshotManager.getLatestSnapshot();
      assert.ok(!('code' in latestResult), 'Should get latest snapshot');
      assert.equal(latestResult.id, createResult.id);
      
      // Cleanup
      rmSync(testDir, { recursive: true, force: true });
    });
    
    test('should handle snapshot not found error', async () => {
      if (!existsSync(testDir)) mkdirSync(testDir, { recursive: true });
      
      const snapshotManager = createSnapshotManager(testDir);
      const mockDb = {
        execute: async () => []
      };
      
      const loadResult = await snapshotManager.loadSnapshot(mockDb, 'non-existent-snapshot');
      assert.ok('code' in loadResult);
      assert.equal(loadResult.code, 'SNAPSHOT_NOT_FOUND');
      
      rmSync(testDir, { recursive: true, force: true });
    });
  });

  describe('Diff Engine', () => {
    test('should calculate deterministic merkle tree', () => {
      const diffEngine = createDiffEngine();
      
      const state: GraphState = {
        nodes: new Map([
          ['n1', { id: 'n1', label: 'Person', properties: { name: 'Alice' } }],
          ['n2', { id: 'n2', label: 'Person', properties: { name: 'Bob' } }]
        ]),
        edges: new Map([
          ['e1', { id: 'e1', from: 'n1', to: 'n2', label: 'KNOWS', properties: {} }]
        ])
      };
      
      const tree1 = diffEngine.calculateMerkleTree(state);
      const tree2 = diffEngine.calculateMerkleTree(state);
      
      assert.equal(tree1.root.hash, tree2.root.hash, 'Same state should produce same hash');
      assert.ok(tree1.root.hash.length === 64, 'SHA256 hash should be 64 chars');
    });
    
    test('should detect differences between states', () => {
      const diffEngine = createDiffEngine();
      
      const state1: GraphState = {
        nodes: new Map([
          ['n1', { id: 'n1', label: 'Person', properties: { name: 'Alice' } }],
          ['n2', { id: 'n2', label: 'Person', properties: { name: 'Bob' } }]
        ]),
        edges: new Map()
      };
      
      const state2: GraphState = {
        nodes: new Map([
          ['n1', { id: 'n1', label: 'Person', properties: { name: 'Alice', age: 30 } }],
          ['n3', { id: 'n3', label: 'Person', properties: { name: 'Charlie' } }]
        ]),
        edges: new Map()
      };
      
      const diff = diffEngine.compareStates(state1, state2);
      
      const added = diff.nodes.filter(n => n.type === 'ADD');
      const updated = diff.nodes.filter(n => n.type === 'UPDATE');
      const deleted = diff.nodes.filter(n => n.type === 'DELETE');
      
      assert.equal(added.length, 1, 'Should detect 1 added node');
      assert.equal(added[0].node.id, 'n3');
      assert.equal(updated.length, 1, 'Should detect 1 modified node');
      assert.equal(updated[0].node.id, 'n1');
      assert.equal(deleted.length, 1, 'Should detect 1 deleted node');
      assert.equal(deleted[0].node.id, 'n2');
    });
    
    test('should generate patches from diff', () => {
      const diffEngine = createDiffEngine();
      
      const state1: GraphState = {
        nodes: new Map([['n1', { id: 'n1', label: 'Person', properties: { name: 'Alice' } }]]),
        edges: new Map()
      };
      
      const state2: GraphState = {
        nodes: new Map([['n1', { id: 'n1', label: 'Person', properties: { name: 'Alice', age: 30 } }]]),
        edges: new Map()
      };
      
      const diff = diffEngine.compareStates(state1, state2);
      const patches = diffEngine.generatePatches(diff);
      
      assert.equal(patches.length, 1, 'Should generate 1 patch');
      assert.equal(patches[0].operation, 'UPDATE');
      assert.equal(patches[0].path, '/nodes/n1');
    });
  });

  describe('Memory Manager', () => {
    test('should monitor memory usage', async () => {
      let thresholdExceeded = false;
      
      const memoryManager = createMemoryManager({
        checkInterval: 100,
        thresholds: {
          heapUsedMB: 1, // Very low threshold for testing
          rssMB: 1
        }
      });
      
      memoryManager.startMonitoring(() => {
        thresholdExceeded = true;
      });
      
      // Wait for monitoring
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // Memory usage should exceed 1MB threshold
      assert.ok(thresholdExceeded, 'Should detect threshold exceeded');
      
      memoryManager.stopMonitoring();
    });
    
    test('should prune old history entries', () => {
      const memoryManager = createMemoryManager({
        checkInterval: 1000,
        thresholds: { heapUsedMB: 512, rssMB: 1024 }
      });
      
      const now = Date.now();
      const history: HistoryEntry[] = [
        { id: '1', timestamp: now - 120000, data: 'old' },
        { id: '2', timestamp: now - 60000, data: 'recent' },
        { id: '3', timestamp: now - 30000, data: 'newer' },
        { id: '4', timestamp: now, data: 'newest' }
      ];
      
      const pruned = memoryManager.pruneHistory(history, {
        keepLatest: 2,
        minAge: 45000
      });
      
      assert.equal(pruned.length, 2, 'Should keep only 2 latest entries');
      assert.equal(pruned[0].id, '4');
      assert.equal(pruned[1].id, '3');
    });
  });
});