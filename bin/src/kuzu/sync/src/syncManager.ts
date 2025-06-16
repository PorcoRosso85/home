/**
 * Server-side Sync Manager for coordinating KuzuDB synchronization
 * Manages version assignment, conflict resolution, and state broadcasting
 */

import type { 
  SyncMessage, 
  ClientId, 
  Version, 
  VersionVector,
  Patch,
  DiffBroadcast,
  SnapshotResponse,
  PatchAck,
  ErrorMessage,
  ConflictInfo
} from './protocol.ts';

import {
  createMessage,
  isSnapshotRequest,
  isPatchSubmit,
  isVersionVectorRequest,
  serializeVersionVector
} from './protocol.ts';

import type { SnapshotManager } from './snapshotManager.ts';
import type { DiffEngine } from './diffEngine.ts';

// Client connection interface
export type ClientConnection = {
  id: ClientId;
  send: (message: SyncMessage) => void;
  close: () => void;
};

// Sync manager configuration
export type SyncManagerConfig = {
  snapshotManager: SnapshotManager;
  diffEngine: DiffEngine;
  maxHistorySize?: number;
};

// Patch history entry
type HistoryEntry = {
  version: Version;
  patches: Patch[];
  clientId: ClientId;
  timestamp: number;
};

// Sync manager interface
export type SyncManager = {
  handleMessage: (clientId: ClientId, message: SyncMessage) => Promise<void>;
  addClient: (connection: ClientConnection) => void;
  removeClient: (clientId: ClientId) => void;
  getCurrentVersion: () => Version;
  getVersionVector: () => VersionVector;
};

// Create sync manager
export function createSyncManager(config: SyncManagerConfig): SyncManager {
  const { snapshotManager, diffEngine, maxHistorySize = 1000 } = config;
  
  // State
  const clients = new Map<ClientId, ClientConnection>();
  const versionVector = new Map<ClientId, Version>();
  const patchHistory: HistoryEntry[] = [];
  let currentVersion: Version = 0;
  
  // Database state (in-memory for now)
  let currentDb = {
    execute: async (query: string) => {
      // This would be replaced with actual KuzuDB instance
      return [];
    }
  };

  // Broadcast message to all clients except sender
  function broadcast(message: SyncMessage, excludeClientId?: ClientId) {
    clients.forEach((connection, clientId) => {
      if (clientId !== excludeClientId) {
        connection.send(message);
      }
    });
  }

  // Handle snapshot request
  async function handleSnapshotRequest(clientId: ClientId, fromVersion?: Version) {
    const connection = clients.get(clientId);
    if (!connection) return;

    try {
      // Create full snapshot
      const snapshotResult = await snapshotManager.createSnapshot(currentDb, currentVersion);
      
      if ('code' in snapshotResult) {
        const error: ErrorMessage = createMessage('ERROR', clientId, {
          code: 'SNAPSHOT_FAILED',
          message: snapshotResult.message
        });
        connection.send(error);
        return;
      }

      // Send snapshot response
      const response: SnapshotResponse = createMessage('SNAPSHOT_RESPONSE', clientId, {
        snapshotId: snapshotResult.id,
        version: currentVersion,
        data: 'CREATE (:TestNode {id: 1});', // Mock data for testing
        incremental: false
      });
      
      connection.send(response);
      
      // Update version vector
      versionVector.set(clientId, currentVersion);
    } catch (error: any) {
      const errorMsg: ErrorMessage = createMessage('ERROR', clientId, {
        code: 'SNAPSHOT_ERROR',
        message: error.message
      });
      connection.send(errorMsg);
    }
  }

  // Handle patch submission
  async function handlePatchSubmit(clientId: ClientId, patches: Patch[], baseVersion: Version) {
    const connection = clients.get(clientId);
    if (!connection) return;

    // Check for version conflict
    if (baseVersion !== currentVersion) {
      const conflict: ConflictInfo = {
        type: 'VERSION_MISMATCH',
        expectedVersion: baseVersion,
        actualVersion: currentVersion,
        conflictingPatches: patches
      };

      const ack: PatchAck = createMessage('PATCH_ACK', clientId, {
        success: false,
        conflict
      });
      
      connection.send(ack);
      return;
    }

    // Assign new version
    currentVersion++;
    
    // Store in history
    patchHistory.push({
      version: currentVersion,
      patches,
      clientId,
      timestamp: Date.now()
    });

    // Trim history if needed
    if (patchHistory.length > maxHistorySize) {
      patchHistory.shift();
    }

    // Send acknowledgment
    const ack: PatchAck = createMessage('PATCH_ACK', clientId, {
      success: true,
      assignedVersion: currentVersion
    });
    connection.send(ack);

    // Broadcast diff to other clients
    const diffBroadcast: DiffBroadcast = createMessage('DIFF_BROADCAST', clientId, {
      version: currentVersion,
      patches,
      sourceClientId: clientId
    });
    broadcast(diffBroadcast, clientId);

    // Update version vector
    versionVector.set(clientId, currentVersion);
  }

  // Handle version vector request
  function handleVersionVectorRequest(clientId: ClientId) {
    const connection = clients.get(clientId);
    if (!connection) return;

    connection.send(createMessage('VERSION_VECTOR_RESPONSE', clientId, {
      vector: serializeVersionVector(versionVector),
      currentVersion
    }));
  }

  // Handle incoming message
  async function handleMessage(clientId: ClientId, message: SyncMessage) {
    if (isSnapshotRequest(message)) {
      await handleSnapshotRequest(clientId, message.fromVersion);
    } else if (isPatchSubmit(message)) {
      await handlePatchSubmit(clientId, message.patches, message.baseVersion);
    } else if (isVersionVectorRequest(message)) {
      handleVersionVectorRequest(clientId);
    }
  }

  // Add client connection
  function addClient(connection: ClientConnection) {
    clients.set(connection.id, connection);
    versionVector.set(connection.id, 0);
  }

  // Remove client connection
  function removeClient(clientId: ClientId) {
    clients.delete(clientId);
    // Keep version vector for history
  }

  return {
    handleMessage,
    addClient,
    removeClient,
    getCurrentVersion: () => currentVersion,
    getVersionVector: () => new Map(versionVector)
  };
}