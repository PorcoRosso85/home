/**
 * Convert patches to Cypher queries
 * SECURITY WARNING: This is a demonstration. In production, use parameterized queries!
 */

import type { GraphPatch, NodePatch, EdgePatch, PropertyPatch } from './types/protocol.ts';
import { isNodePatch, isEdgePatch, isPropertyPatch } from './types/protocol.ts';

export interface CypherQuery {
  statement: string;
  parameters: Record<string, any>;
}

/**
 * Convert a patch to a parameterized Cypher query
 * This approach prevents Cypher injection attacks
 */
export function patchToCypher(patch: GraphPatch): CypherQuery {
  if (isNodePatch(patch)) {
    return convertNodePatch(patch);
  } else if (isEdgePatch(patch)) {
    return convertEdgePatch(patch);
  } else if (isPropertyPatch(patch)) {
    return convertPropertyPatch(patch);
  }
  
  throw new Error(`Unknown patch operation: ${(patch as any).op}`);
}

function convertNodePatch(patch: NodePatch): CypherQuery {
  switch (patch.op) {
    case 'createNode':
      if (!patch.data?.label) {
        throw new Error('Node label is required for createNode');
      }
      
      // Build property string dynamically but safely
      const props = patch.data.properties || {};
      const propKeys = Object.keys(props);
      const propString = propKeys.length > 0
        ? ', ' + propKeys.map(key => `${key}: $${key}`).join(', ')
        : '';
      
      return {
        statement: `CREATE (n:${sanitizeLabel(patch.data.label)} {id: $nodeId${propString}})`,
        parameters: {
          nodeId: patch.nodeId,
          ...props
        }
      };
    
    case 'updateNode':
      if (!patch.data?.properties) {
        throw new Error('Properties are required for updateNode');
      }
      
      const updateProps = patch.data.properties;
      const updateKeys = Object.keys(updateProps);
      const setClause = updateKeys.map(key => `n.${key} = $${key}`).join(', ');
      
      return {
        statement: `MATCH (n {id: $nodeId}) SET ${setClause}`,
        parameters: {
          nodeId: patch.nodeId,
          ...updateProps
        }
      };
    
    case 'deleteNode':
      return {
        statement: 'MATCH (n {id: $nodeId}) DETACH DELETE n',
        parameters: {
          nodeId: patch.nodeId
        }
      };
  }
}

function convertEdgePatch(patch: EdgePatch): CypherQuery {
  switch (patch.op) {
    case 'createEdge':
      if (!patch.data?.label || !patch.data?.fromNodeId || !patch.data?.toNodeId) {
        throw new Error('Edge label and node IDs are required for createEdge');
      }
      
      const edgeProps = patch.data.properties || {};
      const edgePropKeys = Object.keys(edgeProps);
      const edgePropString = edgePropKeys.length > 0
        ? ', ' + edgePropKeys.map(key => `${key}: $${key}`).join(', ')
        : '';
      
      return {
        statement: `
          MATCH (from {id: $fromNodeId})
          MATCH (to {id: $toNodeId})
          CREATE (from)-[e:${sanitizeLabel(patch.data.label)} {id: $edgeId${edgePropString}}]->(to)
        `,
        parameters: {
          fromNodeId: patch.data.fromNodeId,
          toNodeId: patch.data.toNodeId,
          edgeId: patch.edgeId,
          ...edgeProps
        }
      };
    
    case 'updateEdge':
      if (!patch.data?.properties) {
        throw new Error('Properties are required for updateEdge');
      }
      
      const edgeUpdateProps = patch.data.properties;
      const edgeUpdateKeys = Object.keys(edgeUpdateProps);
      const edgeSetClause = edgeUpdateKeys.map(key => `e.${key} = $${key}`).join(', ');
      
      return {
        statement: `MATCH ()-[e {id: $edgeId}]->() SET ${edgeSetClause}`,
        parameters: {
          edgeId: patch.edgeId,
          ...edgeUpdateProps
        }
      };
    
    case 'deleteEdge':
      return {
        statement: 'MATCH ()-[e {id: $edgeId}]->() DELETE e',
        parameters: {
          edgeId: patch.edgeId
        }
      };
  }
}

function convertPropertyPatch(patch: PropertyPatch): CypherQuery {
  const targetVar = patch.targetType === 'node' ? 'n' : 'e';
  
  switch (patch.op) {
    case 'setProperty':
      return {
        statement: `MATCH (${targetVar} {id: $targetId}) SET ${targetVar}.${sanitizePropertyKey(patch.propertyKey)} = $value`,
        parameters: {
          targetId: patch.targetId,
          value: patch.propertyValue
        }
      };
    
    case 'removeProperty':
      return {
        statement: `MATCH (${targetVar} {id: $targetId}) REMOVE ${targetVar}.${sanitizePropertyKey(patch.propertyKey)}`,
        parameters: {
          targetId: patch.targetId
        }
      };
  }
}

/**
 * Sanitize label names to prevent injection
 * Only allow alphanumeric characters and underscores
 */
function sanitizeLabel(label: string): string {
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(label)) {
    throw new Error(`Invalid label: ${label}. Labels must match /^[a-zA-Z_][a-zA-Z0-9_]*$/`);
  }
  return label;
}

/**
 * Sanitize property keys
 */
function sanitizePropertyKey(key: string): string {
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(key)) {
    throw new Error(`Invalid property key: ${key}. Keys must match /^[a-zA-Z_][a-zA-Z0-9_]*$/`);
  }
  return key;
}

/**
 * Batch multiple patches into a single transaction
 */
export function batchPatchesToCypher(patches: GraphPatch[]): CypherQuery[] {
  return patches.map(patch => patchToCypher(patch));
}