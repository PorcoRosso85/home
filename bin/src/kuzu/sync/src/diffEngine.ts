import { createHash } from 'crypto';

// Type definitions
export type NodeId = string;
export type EdgeId = string;

export type GraphNode = {
  id: NodeId;
  label: string;
  properties: Record<string, any>;
};

export type GraphEdge = {
  id: EdgeId;
  from: NodeId;
  to: NodeId;
  label: string;
  properties: Record<string, any>;
};

export type GraphState = {
  nodes: Map<NodeId, GraphNode>;
  edges: Map<EdgeId, GraphEdge>;
};

export type MerkleNode = {
  hash: string;
  children?: Map<string, MerkleNode>;
};

export type MerkleTree = {
  root: MerkleNode;
  nodeHashes: Map<NodeId, string>;
  edgeHashes: Map<EdgeId, string>;
};

export type DiffType = 'add' | 'update' | 'delete';

export type NodeDiff = {
  type: DiffType;
  node: GraphNode;
  oldNode?: GraphNode;
};

export type EdgeDiff = {
  type: DiffType;
  edge: GraphEdge;
  oldEdge?: GraphEdge;
};

export type StateDiff = {
  nodes: NodeDiff[];
  edges: EdgeDiff[];
};

export type Patch = {
  operation: DiffType;
  path: string;
  value?: any;
  oldValue?: any;
};

// DiffEngine interface
export type DiffEngine = {
  calculateMerkleTree: (state: GraphState) => MerkleTree;
  compareStates: (state1: GraphState, state2: GraphState) => StateDiff;
  generatePatches: (diff: StateDiff) => Patch[];
};

// Hash calculation functions
function hashNode(node: GraphNode): string {
  const content = JSON.stringify({
    id: node.id,
    label: node.label,
    properties: node.properties
  });
  return createHash('sha256').update(content).digest('hex');
}

function hashEdge(edge: GraphEdge): string {
  const content = JSON.stringify({
    id: edge.id,
    from: edge.from,
    to: edge.to,
    label: edge.label,
    properties: edge.properties
  });
  return createHash('sha256').update(content).digest('hex');
}

function combineHashes(hashes: string[]): string {
  const combined = hashes.sort().join('');
  return createHash('sha256').update(combined).digest('hex');
}

// Calculate Merkle tree for graph state
export function calculateMerkleTree(state: GraphState): MerkleTree {
  const nodeHashes = new Map<NodeId, string>();
  const edgeHashes = new Map<EdgeId, string>();
  
  // Calculate hashes for all nodes
  state.nodes.forEach((node, nodeId) => {
    nodeHashes.set(nodeId, hashNode(node));
  });
  
  // Calculate hashes for all edges
  state.edges.forEach((edge, edgeId) => {
    edgeHashes.set(edgeId, hashEdge(edge));
  });
  
  // Create root hash from all individual hashes
  const allHashes = [
    ...Array.from(nodeHashes.values()),
    ...Array.from(edgeHashes.values())
  ];
  
  const rootHash = allHashes.length > 0 
    ? combineHashes(allHashes)
    : createHash('sha256').update('empty').digest('hex');
  
  const root: MerkleNode = {
    hash: rootHash
  };
  
  return {
    root,
    nodeHashes,
    edgeHashes
  };
}

// Compare two graph states and detect differences
export function compareStates(state1: GraphState, state2: GraphState): StateDiff {
  const nodeDiffs: NodeDiff[] = [];
  const edgeDiffs: EdgeDiff[] = [];
  
  // Detect added and updated nodes
  state2.nodes.forEach((node2, nodeId) => {
    const node1 = state1.nodes.get(nodeId);
    if (!node1) {
      nodeDiffs.push({ type: 'add', node: node2 });
    } else if (hashNode(node1) !== hashNode(node2)) {
      nodeDiffs.push({ type: 'update', node: node2, oldNode: node1 });
    }
  });
  
  // Detect deleted nodes
  state1.nodes.forEach((node1, nodeId) => {
    if (!state2.nodes.has(nodeId)) {
      nodeDiffs.push({ type: 'delete', node: node1 });
    }
  });
  
  // Detect added and updated edges
  state2.edges.forEach((edge2, edgeId) => {
    const edge1 = state1.edges.get(edgeId);
    if (!edge1) {
      edgeDiffs.push({ type: 'add', edge: edge2 });
    } else if (hashEdge(edge1) !== hashEdge(edge2)) {
      edgeDiffs.push({ type: 'update', edge: edge2, oldEdge: edge1 });
    }
  });
  
  // Detect deleted edges
  state1.edges.forEach((edge1, edgeId) => {
    if (!state2.edges.has(edgeId)) {
      edgeDiffs.push({ type: 'delete', edge: edge1 });
    }
  });
  
  return { nodes: nodeDiffs, edges: edgeDiffs };
}

// Generate patches from state diff
export function generatePatches(diff: StateDiff): Patch[] {
  const patches: Patch[] = [];
  
  // Generate patches for node changes
  diff.nodes.forEach(nodeDiff => {
    switch (nodeDiff.type) {
      case 'add':
        patches.push({
          operation: 'add',
          path: `/nodes/${nodeDiff.node.id}`,
          value: nodeDiff.node
        });
        break;
      case 'update':
        patches.push({
          operation: 'update',
          path: `/nodes/${nodeDiff.node.id}`,
          value: nodeDiff.node,
          oldValue: nodeDiff.oldNode
        });
        break;
      case 'delete':
        patches.push({
          operation: 'delete',
          path: `/nodes/${nodeDiff.node.id}`,
          oldValue: nodeDiff.node
        });
        break;
    }
  });
  
  // Generate patches for edge changes
  diff.edges.forEach(edgeDiff => {
    switch (edgeDiff.type) {
      case 'add':
        patches.push({
          operation: 'add',
          path: `/edges/${edgeDiff.edge.id}`,
          value: edgeDiff.edge
        });
        break;
      case 'update':
        patches.push({
          operation: 'update',
          path: `/edges/${edgeDiff.edge.id}`,
          value: edgeDiff.edge,
          oldValue: edgeDiff.oldEdge
        });
        break;
      case 'delete':
        patches.push({
          operation: 'delete',
          path: `/edges/${edgeDiff.edge.id}`,
          oldValue: edgeDiff.edge
        });
        break;
    }
  });
  
  return patches;
}

// Create DiffEngine instance
export function createDiffEngine(): DiffEngine {
  return {
    calculateMerkleTree,
    compareStates,
    generatePatches
  };
}