/**
 * Snapshot Manager for KuzuDB sync system
 * Handles database export/import operations with R2-compatible storage
 */

import * as fs from 'fs/promises';
import * as path from 'path';

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
export type LoadSnapshotResult = { success: true } | LoadSnapshotError;
export type GetLatestSnapshotResult = SnapshotMetadata | GetLatestSnapshotError;

// Type guards
export function isError<T extends { code: string }>(result: T | any): result is T {
  return 'code' in result && 'message' in result;
}

// Database interface (compatible with kuzu-wasm)
export type KuzuDatabase = {
  execute: (query: string) => Promise<any>;
};

// Snapshot manager interface
export type SnapshotManager = {
  createSnapshot: (db: KuzuDatabase, version: number) => Promise<CreateSnapshotResult>;
  loadSnapshot: (db: KuzuDatabase, snapshotId: string) => Promise<LoadSnapshotResult>;
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

  // Create snapshot implementation using kuzu-wasm
  async function createSnapshot(db: KuzuDatabase, version: number): Promise<CreateSnapshotResult> {
    const snapshotId = `snapshot_${Date.now()}_v${version}`;
    const exportPath = path.join(storageDir, `${snapshotId}.cypher`);

    try {
      // Get schema info first
      const tablesResult = await db.execute('SHOW TABLES');
      
      // Build Cypher export content
      let cypherContent = '';
      
      // Process each table
      for (const tableRow of tablesResult) {
        const tableName = tableRow['name'];
        const tableType = tableRow['type'];
        
        if (tableType === 'NODE') {
          // Export nodes
          const nodesResult = await db.execute(`MATCH (n:${tableName}) RETURN n`);
          
          if (nodesResult && nodesResult.length > 0) {
            for (const row of nodesResult) {
              const node = row['n'];
              
              // Extract properties
              const props = Object.entries(node)
                .filter(([k]) => !k.startsWith('_'))
                .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
                .join(', ');
              
              cypherContent += `CREATE (:${tableName}`;
              if (props) cypherContent += ` {${props}}`;
              cypherContent += ');\n';
            }
          }
        } else if (tableType === 'REL') {
          // Export relationships
          const relsResult = await db.execute(`MATCH ()-[r:${tableName}]->() RETURN r`);
          
          if (relsResult && relsResult.length > 0) {
            for (const row of relsResult) {
              const rel = row['r'];
              
              // For relationships, we need to match the connected nodes
              // This is a simplified version - in reality we'd need node identifiers
              const relProps = Object.entries(rel)
                .filter(([k]) => !k.startsWith('_'))
                .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
                .join(', ');
              
              // Note: This is simplified - actual implementation would need to track node IDs
              cypherContent += `// Relationship: ${tableName}`;
              if (relProps) cypherContent += ` {${relProps}}`;
              cypherContent += '\n';
            }
          }
        }
      }

      // If empty database, create minimal content
      if (!cypherContent) {
        cypherContent = '// Empty database snapshot\n';
      }

      // Write to file
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
        message: `[KuzuDB Export] Failed to create snapshot: ${error.message}`,
        originalError: error.toString()
      };
    }
  }

  // Load snapshot implementation using kuzu-wasm
  async function loadSnapshot(db: KuzuDatabase, snapshotId: string): Promise<LoadSnapshotResult> {
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

      // Clear existing data
      await db.execute('MATCH (n) DETACH DELETE n');

      // Execute each Cypher statement
      const statements = cypherContent.split(';\n').filter(s => s.trim() && !s.trim().startsWith('//'));
      for (const statement of statements) {
        if (statement.trim()) {
          await db.execute(statement);
        }
      }

      return { success: true };
    } catch (error: any) {
      return {
        code: 'IMPORT_FAILED',
        message: `[KuzuDB Import] Failed to load snapshot: ${error.message}`,
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