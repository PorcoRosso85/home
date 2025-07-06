// Causal sync client - Green phase implementation
import { ConflictResolver, LastWriteWinsResolver, ConflictResolutionContext } from './conflict-resolution.ts';

export interface CausalOperation {
  id: string;
  dependsOn: string[];
  type: 'CREATE' | 'UPDATE' | 'DELETE' | 'INCREMENT';
  payload: any;
  clientId: string;
  timestamp: number;
}

export interface CausalSyncClient {
  id: string;
  executeOperation(op: CausalOperation): Promise<CausalOperation>;
  query(cypherQuery: string): Promise<any[]>;
  getOperationHistory(): Promise<CausalOperation[]>;
}

export interface CreateClientOptions {
  clientId: string;
  dbPath: string;
  wsUrl: string;
  conflictResolver?: ConflictResolver;
}

interface InternalClient {
  id: string;
  ws: WebSocket | null;
  operations: Map<string, CausalOperation>;
  appliedOperations: Set<string>;
  pendingOperations: Map<string, CausalOperation>;
  operationHistory: CausalOperation[];
  nodes: Map<string, any>;
  nodeUpdateTimestamps: Map<string, number>; // ノードごとの最終更新タイムスタンプ
  queryResolvers: Map<string, (result: any) => void>;
  conflictResolver: ConflictResolver;
}

// WebSocket接続とクライアント作成
export async function createCausalSyncClient(options: CreateClientOptions): Promise<CausalSyncClient> {
  const client: InternalClient = {
    id: options.clientId,
    ws: null,
    operations: new Map(),
    appliedOperations: new Set(),
    pendingOperations: new Map(),
    operationHistory: [],
    nodes: new Map(),
    nodeUpdateTimestamps: new Map(),
    queryResolvers: new Map(),
    conflictResolver: options.conflictResolver || new LastWriteWinsResolver()
  };

  // WebSocket接続
  const ws = new WebSocket(options.wsUrl);
  client.ws = ws;

  // 接続待機
  await new Promise<void>((resolve, reject) => {
    ws.onopen = () => {
      // クライアントIDを送信
      ws.send(JSON.stringify({
        type: 'identify',
        clientId: options.clientId
      }));
      resolve();
    };
    ws.onerror = reject;
  });

  // メッセージハンドラー
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
      case 'operation':
        handleIncomingOperation(client, message.operation);
        break;
      case 'query_response':
        const resolver = client.queryResolvers.get(message.queryId);
        if (resolver) {
          resolver(message.result);
          client.queryResolvers.delete(message.queryId);
        }
        break;
    }
  };

  const publicClient: CausalSyncClient = {
    id: client.id,
    executeOperation: (op: CausalOperation) => executeOperation(client, op),
    query: (cypherQuery: string) => query(client, cypherQuery),
    getOperationHistory: () => Promise.resolve(client.operationHistory)
  };
  
  // 内部クライアントの参照を保持（disconnect用）
  (publicClient as any)._internal = client;
  
  return publicClient;
}

// 操作を実行
async function executeOperation(client: InternalClient, op: CausalOperation): Promise<CausalOperation> {
  // ローカルに記録
  client.operations.set(op.id, op);
  
  // WebSocket経由で送信
  if (client.ws && client.ws.readyState === WebSocket.OPEN) {
    client.ws.send(JSON.stringify({
      type: 'operation',
      operation: op
    }));
  }
  
  // ローカルで適用を試みる
  await tryApplyOperation(client, op);
  
  return op;
}

// 受信した操作を処理
function handleIncomingOperation(client: InternalClient, op: CausalOperation) {
  if (!client.operations.has(op.id)) {
    client.operations.set(op.id, op);
    tryApplyOperation(client, op);
  }
}


// 操作の適用を試みる
async function tryApplyOperation(client: InternalClient, op: CausalOperation) {
  // すでに適用済みの場合はスキップ
  if (client.appliedOperations.has(op.id)) {
    return;
  }
  
  // 依存関係をチェック
  for (const depId of op.dependsOn) {
    if (!client.appliedOperations.has(depId)) {
      // 依存する操作がまだ適用されていない
      client.pendingOperations.set(op.id, op);
      return;
    }
  }
  
  // 操作を適用
  applyOperationToStore(client, op);
  client.appliedOperations.add(op.id);
  client.operationHistory.push(op);
  
  // この操作に依存している操作を再チェック
  for (const [pendingId, pendingOp] of client.pendingOperations) {
    if (pendingOp.dependsOn.includes(op.id)) {
      client.pendingOperations.delete(pendingId);
      await tryApplyOperation(client, pendingOp);
    }
  }
}

// 操作をストアに適用
function applyOperationToStore(client: InternalClient, op: CausalOperation) {
  switch (op.type) {
    case 'CREATE':
      // CREATE文をパース
      const createMatch = op.payload.cypherQuery.match(/CREATE\s+\((\w+)?:(\w+)\s+\{([^}]+)\}\)/);
      if (createMatch) {
        const [, varName, nodeType, propsStr] = createMatch;
        const props = parseProperties(propsStr);
        const nodeId = props.id || crypto.randomUUID();
        client.nodes.set(nodeId, {
          type: nodeType,
          properties: props
        });
      }
      break;
      
    case 'INCREMENT':
      // インクリメント操作
      const node = client.nodes.get(op.payload.nodeId);
      if (node) {
        const prop = op.payload.property;
        node.properties[prop] = (node.properties[prop] || 0) + op.payload.delta;
      }
      break;
      
    case 'UPDATE':
      // UPDATE文をパース - SETの前にMATCH部分からノードIDを取得
      const fullUpdateMatch = op.payload.cypherQuery.match(/MATCH\s+\((\w+):(\w+)\s+\{id:\s*'([^']+)'\}\)\s+SET\s+(\w+)\.(\w+)\s*=\s*(.+)/);
      if (fullUpdateMatch) {
        const [, varName, nodeType, nodeId, setVar, prop, value] = fullUpdateMatch;
        
        // 競合解決コンテキストを準備
        const updateKey = `${nodeId}.${prop}`;
        const lastTimestamp = client.nodeUpdateTimestamps.get(updateKey);
        const node = client.nodes.get(nodeId);
        
        const context: ConflictResolutionContext = {
          nodeId,
          property: prop,
          nodeType,
          existingValue: node?.properties[prop],
          existingTimestamp: lastTimestamp
        };
        
        // 競合解決アルゴリズムに判定を委譲
        const shouldApply = client.conflictResolver.shouldApplyUpdate(
          {
            timestamp: op.timestamp,
            value: value,
            dependsOn: op.dependsOn
          },
          context
        );
        
        if (!shouldApply) {
          return;
        }
        
        if (node && node.type === nodeType) {
          // 値の処理（文字列の場合はクォートを除去、数値の場合は変換）
          let finalValue = value.trim();
          if (finalValue.startsWith("'") && finalValue.endsWith("'")) {
            finalValue = finalValue.slice(1, -1);
          } else if (!isNaN(Number(finalValue))) {
            finalValue = Number(finalValue);
          }
          node.properties[prop] = finalValue;
          
          // タイムスタンプを更新
          client.nodeUpdateTimestamps.set(updateKey, op.timestamp);
        }
      }
      break;
  }
}

// プロパティ文字列をパース
function parseProperties(propsStr: string): any {
  const props: any = {};
  const pairs = propsStr.split(',');
  for (const pair of pairs) {
    const [key, value] = pair.trim().split(':').map(s => s.trim());
    if (value.startsWith("'") && value.endsWith("'")) {
      props[key] = value.slice(1, -1);
    } else {
      props[key] = isNaN(Number(value)) ? value : Number(value);
    }
  }
  return props;
}

// クエリを実行
async function query(client: InternalClient, cypherQuery: string): Promise<any[]> {
  // 簡易的なクエリパーサー
  
  // MATCH (c:Counter {id: 'shared-counter'}) RETURN c.value as value
  const counterMatch = cypherQuery.match(/MATCH\s+\((\w+):(\w+)\s+\{id:\s*'([^']+)'\}\)\s+RETURN\s+(\w+)\.(\w+)\s+as\s+(\w+)/);
  if (counterMatch) {
    const [, varName, nodeType, nodeId, returnVar, prop, alias] = counterMatch;
    const node = client.nodes.get(nodeId);
    if (node && node.type === nodeType) {
      return [{ [alias]: node.properties[prop] }];
    }
  }
  
  // MATCH (n:Node {id: 'test-node'}) RETURN n.status as status
  const statusMatch = cypherQuery.match(/MATCH\s+\((\w+):(\w+)\s+\{id:\s*'([^']+)'\}\)\s+RETURN\s+(\w+)\.(\w+)\s+as\s+(\w+)/);
  if (statusMatch) {
    const [, varName, nodeType, nodeId, returnVar, prop, alias] = statusMatch;
    const node = client.nodes.get(nodeId);
    if (node && node.type === nodeType) {
      return [{ [alias]: node.properties[prop] }];
    }
  }
  
  // MATCH (n:Chain {id: 'chain'}) RETURN n.step as step
  const chainMatch = cypherQuery.match(/MATCH\s+\((\w+):(\w+)\s+\{id:\s*'([^']+)'\}\)\s+RETURN\s+(\w+)\.(\w+)\s+as\s+(\w+)/);
  if (chainMatch) {
    const [, varName, nodeType, nodeId, returnVar, prop, alias] = chainMatch;
    const node = client.nodes.get(nodeId);
    if (node && node.type === nodeType) {
      return [{ [alias]: node.properties[prop] }];
    }
  }
  
  return [];
}

// 切断
export async function disconnect(client: CausalSyncClient): Promise<void> {
  const internal = (client as any)._internal as InternalClient;
  if (internal && internal.ws) {
    internal.ws.close();
  }
}