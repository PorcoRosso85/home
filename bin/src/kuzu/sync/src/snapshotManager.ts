/**
 * Snapshot Manager for KuzuDB sync system
 * Generates Cypher snapshots from patch history
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import type { GraphPatch } from './types/protocol.ts';
import { patchToCypher } from './patchToCypher.ts';

// Error types using union types pattern
export type CreateSnapshotError = {
  code: 'EXPORT_FAILED';
  message: string;
  originalError?: string;
};

export type LoadSnapshotError = {
  code: 'IMPORT_FAILED' | 'SNAPSHOT_NOT_FOUND';
  message: string;
  originalError?: string;
};

export type GetLatestSnapshotError = {
  code: 'NO_SNAPSHOTS' | 'READ_ERROR';
  message: string;
};

// Snapshot metadata type
export type SnapshotMetadata = {
  id: string;
  timestamp: number;
  version: number;
  size: number;
  path: string;
};

// Success result types
export type CreateSnapshotResult = SnapshotMetadata | CreateSnapshotError;
export type LoadSnapshotResult = { success: true; content: string } | LoadSnapshotError;
export type GetLatestSnapshotResult = SnapshotMetadata | GetLatestSnapshotError;

// Type guards
export function isError<T extends { code: string }>(result: T | any): result is T {
  return 'code' in result && 'message' in result;
}

// Patch history entry
export type PatchHistoryEntry = {
  version: number;
  patches: GraphPatch[];
  clientId: string;
  timestamp: number;
};

// Snapshot manager interface
export type SnapshotManager = {
  createSnapshot: (patchHistory: PatchHistoryEntry[], version: number) => Promise<CreateSnapshotResult>;
  loadSnapshot: (snapshotId: string) => Promise<LoadSnapshotResult>;
  getLatestSnapshot: () => Promise<GetLatestSnapshotResult>;
};

// Create snapshot manager with dependencies
export function createSnapshotManager(storageDir: string): SnapshotManager {
  const metadataPath = path.join(storageDir, 'snapshots.json');

  // Read snapshot metadata
  async function readMetadata(): Promise<SnapshotMetadata[]> {
    try {
      const data = await fs.readFile(metadataPath, 'utf-8');
      return JSON.parse(data);
    } catch {
      return [];
    }
  }

  // Write snapshot metadata
  async function writeMetadata(metadata: SnapshotMetadata[]): Promise<void> {
    await fs.mkdir(storageDir, { recursive: true });
    await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2));
  }

  // Create snapshot implementation from patch history
  async function createSnapshot(patchHistory: PatchHistoryEntry[], version: number): Promise<CreateSnapshotResult> {
    const snapshotId = `snapshot_${Date.now()}_v${version}`;
    const exportPath = path.join(storageDir, `${snapshotId}.cypher`);

    try {
      // Build Cypher content from patch history
      let cypherContent = `-- KuzuDB Snapshot v${version}\n`;
      cypherContent += `-- Generated at ${new Date().toISOString()}\n`;
      cypherContent += `-- Total patches: ${patchHistory.reduce((sum, entry) => sum + entry.patches.length, 0)}\n\n`;
      
      // Track created entities to avoid duplicates
      const createdNodes = new Set<string>();
      const createdEdges = new Set<string>();
      const deletedNodes = new Set<string>();
      const deletedEdges = new Set<string>();
      
      // Process patches in order
      for (const entry of patchHistory) {
        cypherContent += `\n-- Version ${entry.version} by ${entry.clientId}\n`;
        
        for (const patch of entry.patches) {
          try {
            // Skip if entity was deleted
            if (patch.op === 'deleteNode' && 'nodeId' in patch) {
              deletedNodes.add(patch.nodeId);
              createdNodes.delete(patch.nodeId);
              continue;
            }
            if (patch.op === 'deleteEdge' && 'edgeId' in patch) {
              deletedEdges.add(patch.edgeId);
              createdEdges.delete(patch.edgeId);
              continue;
            }
            
            // Skip if trying to update/create a deleted entity
            if ('nodeId' in patch && deletedNodes.has(patch.nodeId)) continue;
            if ('edgeId' in patch && deletedEdges.has(patch.edgeId)) continue;
            
            // Convert patch to Cypher
            const cypherQuery = patchToCypher(patch);
            
            // For create operations, track the entity
            if (patch.op === 'createNode' && 'nodeId' in patch) {
              if (createdNodes.has(patch.nodeId)) continue; // Skip duplicate creates
              createdNodes.add(patch.nodeId);
            }
            if (patch.op === 'createEdge' && 'edgeId' in patch) {
              if (createdEdges.has(patch.edgeId)) continue; // Skip duplicate creates
              createdEdges.add(patch.edgeId);
            }
            
            // Add the Cypher statement
            cypherContent += cypherQuery.statement;
            
            // Add parameters as comments for clarity
            if (Object.keys(cypherQuery.parameters).length > 0) {
              cypherContent += ` -- params: ${JSON.stringify(cypherQuery.parameters)}`;
            }
            cypherContent += '\n';
            
          } catch (patchError: any) {
            // Log patch conversion errors but continue
            cypherContent += `-- Error converting patch: ${patchError.message}\n`;
            cypherContent += `-- Patch: ${JSON.stringify(patch)}\n`;
          }
        }
      }

      // If no valid operations, create minimal content
      if (createdNodes.size === 0 && createdEdges.size === 0) {
        cypherContent += '\n-- Empty database (no entities created)\n';
      }

      // Write to file
      await fs.mkdir(storageDir, { recursive: true });
      await fs.writeFile(exportPath, cypherContent, 'utf-8');

      // Get file size
      const stats = await fs.stat(exportPath);

      // Create metadata
      const metadata: SnapshotMetadata = {
        id: snapshotId,
        timestamp: Date.now(),
        version,
        size: stats.size,
        path: exportPath
      };

      // Update metadata file
      const allMetadata = await readMetadata();
      allMetadata.push(metadata);
      await writeMetadata(allMetadata);

      return metadata;
    } catch (error: any) {
      return {
        code: 'EXPORT_FAILED',
        message: `[Snapshot Creation] Failed to create snapshot: ${error.message}`,
        originalError: error.toString()
      };
    }
  }

  // Load snapshot implementation - returns Cypher content
  async function loadSnapshot(snapshotId: string): Promise<LoadSnapshotResult> {
    try {
      // Find snapshot metadata
      const allMetadata = await readMetadata();
      const snapshot = allMetadata.find(s => s.id === snapshotId);

      if (!snapshot) {
        return {
          code: 'SNAPSHOT_NOT_FOUND',
          message: `[Snapshot Manager] Snapshot ${snapshotId} not found`
        };
      }

      // Check if snapshot file exists
      await fs.access(snapshot.path);

      // Read Cypher content
      const cypherContent = await fs.readFile(snapshot.path, 'utf-8');

      return { success: true, content: cypherContent };
    } catch (error: any) {
      return {
        code: 'IMPORT_FAILED',
        message: `[Snapshot Load] Failed to load snapshot: ${error.message}`,
        originalError: error.toString()
      };
    }
  }

  // Get latest snapshot implementation
  async function getLatestSnapshot(): Promise<GetLatestSnapshotResult> {
    try {
      const allMetadata = await readMetadata();

      if (allMetadata.length === 0) {
        return {
          code: 'NO_SNAPSHOTS',
          message: '[Snapshot Manager] No snapshots available'
        };
      }

      // Sort by timestamp descending and return latest
      const sorted = allMetadata.sort((a, b) => b.timestamp - a.timestamp);
      return sorted[0];
    } catch (error: any) {
      return {
        code: 'READ_ERROR',
        message: `[Snapshot Manager] Failed to read snapshots: ${error.message}`
      };
    }
  }

  return {
    createSnapshot,
    loadSnapshot,
    getLatestSnapshot
  };
}