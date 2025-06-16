/**
 * Conflict Resolution for Graph Operations
 * Implements the rules defined in PROTOCOL.md
 */

import { GraphPatch, isNodePatch, isEdgePatch } from './types/protocol';

export interface GraphState {
  nodes: Map<string, NodeState>;
  edges: Map<string, EdgeState>;
  version: number;
}

export interface NodeState {
  id: string;
  label: string;
  properties: Record<string, any>;
  isDeleted: boolean;
  lastModified: number;
  createdBy: string;
}

export interface EdgeState {
  id: string;
  label: string;
  fromNodeId: string;
  toNodeId: string;
  properties: Record<string, any>;
  isDeleted: boolean;
  lastModified: number;
  createdBy: string;
}

export interface ConflictResolution {
  action: 'accept' | 'reject' | 'modify';
  reason?: string;
  modifiedPatch?: GraphPatch;
}

export class ConflictResolver {
  constructor(private state: GraphState) {}

  /**
   * Resolve conflicts for a given patch
   */
  resolve(patch: GraphPatch): ConflictResolution {
    if (isNodePatch(patch)) {
      return this.resolveNodePatch(patch);
    } else if (isEdgePatch(patch)) {
      return this.resolveEdgePatch(patch);
    } else {
      return this.resolvePropertyPatch(patch);
    }
  }

  private resolveNodePatch(patch: NodePatch): ConflictResolution {
    const existingNode = this.state.nodes.get(patch.nodeId);

    switch (patch.op) {
      case 'create_node':
        // Rule 1: Duplicate node creation
        if (existingNode && !existingNode.isDeleted) {
          return {
            action: 'reject',
            reason: 'node_already_exists'
          };
        }
        
        // Allow creation if node was deleted (resurrection)
        if (existingNode && existingNode.isDeleted) {
          return {
            action: 'modify',
            reason: 'resurrecting_deleted_node',
            modifiedPatch: {
              ...patch,
              op: 'update_node' // Change to update instead
            }
          };
        }
        
        return { action: 'accept' };

      case 'update_node':
        // Rule 3: Operations on deleted nodes
        if (!existingNode || existingNode.isDeleted) {
          return {
            action: 'reject',
            reason: 'node_not_found_or_deleted'
          };
        }
        
        // Rule 2: Last-Write-Wins for updates
        if (patch.timestamp <= existingNode.lastModified) {
          return {
            action: 'reject',
            reason: 'stale_update'
          };
        }
        
        return { action: 'accept' };

      case 'delete_node':
        if (!existingNode || existingNode.isDeleted) {
          return {
            action: 'reject',
            reason: 'node_not_found_or_already_deleted'
          };
        }
        
        // Check for dependent edges
        const dependentEdges = this.findEdgesForNode(patch.nodeId);
        if (dependentEdges.length > 0) {
          // Automatically cascade delete edges
          return {
            action: 'modify',
            reason: 'cascading_edge_deletion',
            modifiedPatch: patch // Server will handle cascade
          };
        }
        
        return { action: 'accept' };
    }
  }

  private resolveEdgePatch(patch: EdgePatch): ConflictResolution {
    const existingEdge = this.state.edges.get(patch.edgeId);

    switch (patch.op) {
      case 'create_edge':
        // Check edge already exists
        if (existingEdge && !existingEdge.isDeleted) {
          return {
            action: 'reject',
            reason: 'edge_already_exists'
          };
        }
        
        // Rule 4: Reference integrity
        if (!patch.data?.fromNodeId || !patch.data?.toNodeId) {
          return {
            action: 'reject',
            reason: 'missing_node_references'
          };
        }
        
        const fromNode = this.state.nodes.get(patch.data.fromNodeId);
        const toNode = this.state.nodes.get(patch.data.toNodeId);
        
        if (!fromNode || fromNode.isDeleted || !toNode || toNode.isDeleted) {
          return {
            action: 'reject',
            reason: 'invalid_node_reference'
          };
        }
        
        // Check for duplicate edges (same label between same nodes)
        const duplicateEdge = this.findDuplicateEdge(
          patch.data.fromNodeId,
          patch.data.toNodeId,
          patch.data.label || ''
        );
        
        if (duplicateEdge) {
          return {
            action: 'reject',
            reason: 'duplicate_edge'
          };
        }
        
        return { action: 'accept' };

      case 'update_edge':
        if (!existingEdge || existingEdge.isDeleted) {
          return {
            action: 'reject',
            reason: 'edge_not_found_or_deleted'
          };
        }
        
        // LWW for edge updates
        if (patch.timestamp <= existingEdge.lastModified) {
          return {
            action: 'reject',
            reason: 'stale_update'
          };
        }
        
        return { action: 'accept' };

      case 'delete_edge':
        if (!existingEdge || existingEdge.isDeleted) {
          return {
            action: 'reject',
            reason: 'edge_not_found_or_already_deleted'
          };
        }
        
        return { action: 'accept' };
    }
  }

  private resolvePropertyPatch(patch: PropertyPatch): ConflictResolution {
    const target = patch.targetType === 'node' 
      ? this.state.nodes.get(patch.targetId)
      : this.state.edges.get(patch.targetId);
    
    if (!target || target.isDeleted) {
      return {
        action: 'reject',
        reason: `${patch.targetType}_not_found_or_deleted`
      };
    }
    
    // Rule 5: Property type validation (simplified)
    if (patch.op === 'set_property' && patch.propertyValue !== undefined) {
      // Add your schema validation here
      if (!this.validatePropertyType(patch.propertyKey, patch.propertyValue)) {
        return {
          action: 'reject',
          reason: 'invalid_property_type'
        };
      }
    }
    
    return { action: 'accept' };
  }

  private findEdgesForNode(nodeId: string): EdgeState[] {
    const edges: EdgeState[] = [];
    this.state.edges.forEach(edge => {
      if (!edge.isDeleted && 
          (edge.fromNodeId === nodeId || edge.toNodeId === nodeId)) {
        edges.push(edge);
      }
    });
    return edges;
  }

  private findDuplicateEdge(fromNodeId: string, toNodeId: string, label: string): EdgeState | undefined {
    for (const edge of this.state.edges.values()) {
      if (!edge.isDeleted &&
          edge.fromNodeId === fromNodeId &&
          edge.toNodeId === toNodeId &&
          edge.label === label) {
        return edge;
      }
    }
    return undefined;
  }

  private validatePropertyType(key: string, value: any): boolean {
    // Implement your schema validation here
    // For now, just basic type checks
    
    // Reserved properties
    if (['id', 'label', 'isDeleted', 'lastModified'].includes(key)) {
      return false;
    }
    
    // Basic type validation
    const valueType = typeof value;
    if (!['string', 'number', 'boolean'].includes(valueType) && 
        value !== null && 
        !Array.isArray(value) && 
        !(value instanceof Date)) {
      return false;
    }
    
    return true;
  }
}

/**
 * Apply a patch to the state (after conflict resolution)
 */
export function applyPatch(state: GraphState, patch: GraphPatch): GraphState {
  const newState = {
    nodes: new Map(state.nodes),
    edges: new Map(state.edges),
    version: state.version + 1
  };

  if (isNodePatch(patch)) {
    switch (patch.op) {
      case 'create_node':
        newState.nodes.set(patch.nodeId, {
          id: patch.nodeId,
          label: patch.data?.label || 'Node',
          properties: patch.data?.properties || {},
          isDeleted: false,
          lastModified: patch.timestamp,
          createdBy: patch.clientId
        });
        break;
      
      case 'update_node':
        const node = newState.nodes.get(patch.nodeId)!;
        if (patch.data?.label) node.label = patch.data.label;
        if (patch.data?.properties) {
          node.properties = { ...node.properties, ...patch.data.properties };
        }
        node.lastModified = patch.timestamp;
        break;
      
      case 'delete_node':
        const nodeToDelete = newState.nodes.get(patch.nodeId)!;
        nodeToDelete.isDeleted = true;
        nodeToDelete.lastModified = patch.timestamp;
        
        // Cascade delete edges
        newState.edges.forEach(edge => {
          if (edge.fromNodeId === patch.nodeId || edge.toNodeId === patch.nodeId) {
            edge.isDeleted = true;
            edge.lastModified = patch.timestamp;
          }
        });
        break;
    }
  } else if (isEdgePatch(patch)) {
    switch (patch.op) {
      case 'create_edge':
        newState.edges.set(patch.edgeId, {
          id: patch.edgeId,
          label: patch.data?.label || 'Edge',
          fromNodeId: patch.data?.fromNodeId!,
          toNodeId: patch.data?.toNodeId!,
          properties: patch.data?.properties || {},
          isDeleted: false,
          lastModified: patch.timestamp,
          createdBy: patch.clientId
        });
        break;
      
      case 'update_edge':
        const edge = newState.edges.get(patch.edgeId)!;
        if (patch.data?.label) edge.label = patch.data.label;
        if (patch.data?.properties) {
          edge.properties = { ...edge.properties, ...patch.data.properties };
        }
        edge.lastModified = patch.timestamp;
        break;
      
      case 'delete_edge':
        const edgeToDelete = newState.edges.get(patch.edgeId)!;
        edgeToDelete.isDeleted = true;
        edgeToDelete.lastModified = patch.timestamp;
        break;
    }
  } else {
    // Property patch
    const target = patch.targetType === 'node' 
      ? newState.nodes.get(patch.targetId)
      : newState.edges.get(patch.targetId);
    
    if (target) {
      if (patch.op === 'set_property') {
        target.properties[patch.propertyKey] = patch.propertyValue;
      } else {
        delete target.properties[patch.propertyKey];
      }
      target.lastModified = patch.timestamp;
    }
  }

  return newState;
}