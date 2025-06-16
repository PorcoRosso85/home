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

import type { SnapshotManager, PatchHistoryEntry } from './snapshotManager.ts';
import type { DiffEngine } from './diffEngine.ts';
import type { GraphPatch } from './types/protocol.ts';

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


// Sync manager interface
export type SyncManager = {
  handleMessage: (clientId: ClientId, message: SyncMessage) => Promise<void>;
  addClient: (connection: ClientConnection) => void;
  removeClient: (clientId: ClientId) => void;
  getCurrentVersion: () => Version;
  getVersionVector: () => VersionVector;
};

// Convert protocol Patch to GraphPatch
function convertToGraphPatch(patch: Patch, clientId: ClientId): GraphPatch | null {
  const basePatch = {
    id: patch.id,
    timestamp: Date.now(),
    clientId
  };

  // Parse the path to extract entity type and ID
  const pathParts = patch.path.split('/').filter(p => p);
  if (pathParts.length < 2) return null;

  const [entityType, entityId] = pathParts;

  switch (patch.operation) {
    case 'CREATE_NODE':
      return {
        ...basePatch,
        op: 'create_node',
        nodeId: entityId,
        data: {
          label: patch.value?.label || 'Node',
          properties: patch.value?.properties || {}
        }
      };
    
    case 'DELETE_NODE':
      return {
        ...basePatch,
        op: 'delete_node',
        nodeId: entityId
      };
    
    case 'CREATE_EDGE':
      return {
        ...basePatch,
        op: 'create_edge',
        edgeId: entityId,
        data: {
          label: patch.value?.label || 'Edge',
          fromNodeId: patch.value?.fromNodeId,
          toNodeId: patch.value?.toNodeId,
          properties: patch.value?.properties || {}
        }
      };
    
    case 'DELETE_EDGE':
      return {
        ...basePatch,
        op: 'delete_edge',
        edgeId: entityId
      };
    
    case 'SET_PROPERTY':
      if (!patch.property) return null;
      return {
        ...basePatch,
        op: 'set_property',
        targetType: entityType === 'nodes' ? 'node' : 'edge',
        targetId: entityId,
        propertyKey: patch.property,
        propertyValue: patch.value
      };
    
    case 'REMOVE_PROPERTY':
      if (!patch.property) return null;
      return {
        ...basePatch,
        op: 'remove_property',
        targetType: entityType === 'nodes' ? 'node' : 'edge',
        targetId: entityId,
        propertyKey: patch.property
      };
    
    default:
      return null;
  }
}

// Create sync manager
export function createSyncManager(config: SyncManagerConfig): SyncManager {
  const { snapshotManager, diffEngine, maxHistorySize = 1000 } = config;
  
  // State
  const clients = new Map<ClientId, ClientConnection>();
  const versionVector = new Map<ClientId, Version>();
  const patchHistory: PatchHistoryEntry[] = [];
  let currentVersion: Version = 0;
  
  // Note: Server no longer maintains a database instance
  // It only tracks patch history and generates snapshots from it

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
      // Create full snapshot from patch history
      const snapshotResult = await snapshotManager.createSnapshot(patchHistory, currentVersion);
      
      if ('code' in snapshotResult) {
        const error: ErrorMessage = createMessage('ERROR', clientId, {
          code: 'SNAPSHOT_FAILED',
          message: snapshotResult.message
        });
        connection.send(error);
        return;
      }

      // Load the snapshot content
      const loadResult = await snapshotManager.loadSnapshot(snapshotResult.id);
      
      if ('code' in loadResult) {
        const error: ErrorMessage = createMessage('ERROR', clientId, {
          code: 'SNAPSHOT_FAILED',
          message: loadResult.message
        });
        connection.send(error);
        return;
      }

      // Send snapshot response with Cypher content
      const response: SnapshotResponse = createMessage('SNAPSHOT_RESPONSE', clientId, {
        snapshotId: snapshotResult.id,
        version: currentVersion,
        data: loadResult.content,
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

    // Convert patches to GraphPatch format
    const graphPatches: GraphPatch[] = [];
    for (const patch of patches) {
      const graphPatch = convertToGraphPatch(patch, clientId);
      if (graphPatch) {
        graphPatches.push(graphPatch);
      }
    }

    // Assign new version
    currentVersion++;
    
    // Store in history
    patchHistory.push({
      version: currentVersion,
      patches: graphPatches,
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