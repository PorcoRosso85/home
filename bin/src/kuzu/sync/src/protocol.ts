/**
 * Sync Protocol Messages for KuzuDB synchronization
 * Server-assigned version numbers for consistency
 */

// Base message types
export type MessageType = 
  | 'SNAPSHOT_REQUEST'
  | 'SNAPSHOT_RESPONSE'
  | 'DIFF_BROADCAST'
  | 'VERSION_VECTOR_REQUEST'
  | 'VERSION_VECTOR_RESPONSE'
  | 'PATCH_SUBMIT'
  | 'PATCH_ACK'
  | 'ERROR';

// Client identification
export type ClientId = string;
export type Version = number;

// Version vector for tracking state across clients
export type VersionVector = Map<ClientId, Version>;

// Base message structure
export type BaseMessage = {
  type: MessageType;
  clientId: ClientId;
  timestamp: number;
};

// Snapshot request/response messages
export type SnapshotRequest = BaseMessage & {
  type: 'SNAPSHOT_REQUEST';
  fromVersion?: Version; // Request incremental if possible
};

export type SnapshotResponse = BaseMessage & {
  type: 'SNAPSHOT_RESPONSE';
  snapshotId: string;
  version: Version;
  data: string; // Cypher statements
  incremental: boolean;
};

// Diff broadcast for real-time sync
export type DiffBroadcast = BaseMessage & {
  type: 'DIFF_BROADCAST';
  version: Version; // Server-assigned version
  patches: Patch[];
  sourceClientId: ClientId;
};

// Version vector for consistency checking
export type VersionVectorRequest = BaseMessage & {
  type: 'VERSION_VECTOR_REQUEST';
};

export type VersionVectorResponse = BaseMessage & {
  type: 'VERSION_VECTOR_RESPONSE';
  vector: Record<ClientId, Version>; // Serializable version of Map
  currentVersion: Version;
};

// Patch submission from client
export type PatchSubmit = BaseMessage & {
  type: 'PATCH_SUBMIT';
  patches: Patch[];
  baseVersion: Version; // Version this patch is based on
};

export type PatchAck = BaseMessage & {
  type: 'PATCH_ACK';
  success: boolean;
  assignedVersion?: Version;
  conflict?: ConflictInfo;
};

// Error message
export type ErrorMessage = BaseMessage & {
  type: 'ERROR';
  code: string;
  message: string;
  details?: any;
};

// Patch types for property-level operations
export type PatchOperation = 
  | 'CREATE_NODE'
  | 'DELETE_NODE'
  | 'SET_PROPERTY'
  | 'REMOVE_PROPERTY'
  | 'CREATE_EDGE'
  | 'DELETE_EDGE';

export type Patch = {
  id: string;
  operation: PatchOperation;
  path: string; // e.g., /nodes/n1, /edges/e1
  property?: string; // For property operations
  value?: any;
  oldValue?: any; // For conflict detection
};

// Conflict information
export type ConflictInfo = {
  type: 'VERSION_MISMATCH' | 'CONCURRENT_EDIT' | 'DELETED_TARGET';
  expectedVersion: Version;
  actualVersion: Version;
  conflictingPatches: Patch[];
};

// Union type for all messages
export type SyncMessage = 
  | SnapshotRequest
  | SnapshotResponse
  | DiffBroadcast
  | VersionVectorRequest
  | VersionVectorResponse
  | PatchSubmit
  | PatchAck
  | ErrorMessage;

// Type guards
export function isSnapshotRequest(msg: SyncMessage): msg is SnapshotRequest {
  return msg.type === 'SNAPSHOT_REQUEST';
}

export function isSnapshotResponse(msg: SyncMessage): msg is SnapshotResponse {
  return msg.type === 'SNAPSHOT_RESPONSE';
}

export function isDiffBroadcast(msg: SyncMessage): msg is DiffBroadcast {
  return msg.type === 'DIFF_BROADCAST';
}

export function isPatchSubmit(msg: SyncMessage): msg is PatchSubmit {
  return msg.type === 'PATCH_SUBMIT';
}

export function isPatchAck(msg: SyncMessage): msg is PatchAck {
  return msg.type === 'PATCH_ACK';
}

export function isError(msg: SyncMessage): msg is ErrorMessage {
  return msg.type === 'ERROR';
}

export function isVersionVectorRequest(msg: SyncMessage): msg is VersionVectorRequest {
  return msg.type === 'VERSION_VECTOR_REQUEST';
}

export function isVersionVectorResponse(msg: SyncMessage): msg is VersionVectorResponse {
  return msg.type === 'VERSION_VECTOR_RESPONSE';
}

// Helper functions
export function createMessage<T extends SyncMessage>(
  type: MessageType,
  clientId: ClientId,
  data: Omit<T, 'type' | 'clientId' | 'timestamp'>
): T {
  return {
    type,
    clientId,
    timestamp: Date.now(),
    ...data
  } as T;
}

export function serializeVersionVector(vector: VersionVector): Record<ClientId, Version> {
  const record: Record<ClientId, Version> = {};
  vector.forEach((version, clientId) => {
    record[clientId] = version;
  });
  return record;
}

export function deserializeVersionVector(record: Record<ClientId, Version>): VersionVector {
  const vector = new Map<ClientId, Version>();
  Object.entries(record).forEach(([clientId, version]) => {
    vector.set(clientId, version);
  });
  return vector;
}