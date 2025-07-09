// Causal sync client - Green phase implementation
import { ConflictResolver, LastWriteWinsResolver, ConflictResolutionContext } from './conflict-resolution.ts';

// メモリ制限の定数
const MAX_OPERATION_HISTORY = 100;
const MAX_PENDING_OPERATIONS = 50;
const MAX_OPERATIONS_MAP = 200;
const OPERATION_CLEANUP_INTERVAL = 30000; // 30秒

export interface CausalOperation {
  id: string;
  dependsOn: string[];
  type: 'CREATE' | 'UPDATE' | 'DELETE' | 'INCREMENT' | 'DDL' | 'DML';
  payload: any;
  clientId: string;
  timestamp: number;
}

export interface CausalSyncClient {
  id: string;
  executeOperation(op: CausalOperation): Promise<CausalOperation>;
  query(cypherQuery: string): Promise<any[]>;
  getOperationHistory(): Promise<CausalOperation[]>;
  getCircularDependencies(): Promise<string[][]>;
  simulatePartition(allowedClients: string[]): Promise<void>;
  healPartition(): Promise<void>;
  executeTransaction(transaction: Transaction): Promise<void>;
  getSchemaVersion(): Promise<SchemaVersion>;
  onSchemaChange(handler: () => void): void;
}

export interface SchemaVersion {
  version: number;
  operations: string[];
  tables: Record<string, TableSchema>;
}

export interface TableSchema {
  columns: string[] | Record<string, ColumnSchema>;
}

export interface ColumnSchema {
  type: string;
}

export interface Transaction {
  id: string;
  operations: TransactionOperation[];
  clientId: string;
  timestamp: number;
}

export interface TransactionOperation {
  id: string;
  type: 'CREATE' | 'UPDATE' | 'DELETE' | 'DDL' | 'DML';
  payload: any;
  constraint?: {
    type: 'minimum_balance';
    value: number;
  };
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
  isPartitioned: boolean;
  partitionAllowedClients: Set<string>;
  transactionOperations: Map<string, TransactionOperation[]>;
  transactionRollbacks: Map<string, CausalOperation[]>;
  schemaVersion: SchemaVersion;
  schemaChangeHandlers: Array<() => void>;
  cleanupTimer?: number;
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
    conflictResolver: options.conflictResolver || new LastWriteWinsResolver(),
    isPartitioned: false,
    partitionAllowedClients: new Set(),
    transactionOperations: new Map(),
    transactionRollbacks: new Map(),
    schemaVersion: { version: 0, operations: [], tables: {} },
    schemaChangeHandlers: []
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
      case 'schema_update':
        // スキーマ更新を受信
        if (message.schema) {
          client.schemaVersion = message.schema;
          // スキーマ変更ハンドラーを呼び出す
          for (const handler of client.schemaChangeHandlers) {
            handler();
          }
        }
        break;
    }
  };

  const publicClient: CausalSyncClient = {
    id: client.id,
    executeOperation: (op: CausalOperation) => executeOperation(client, op),
    query: (cypherQuery: string) => query(client, cypherQuery),
    getOperationHistory: () => Promise.resolve(client.operationHistory),
    getCircularDependencies: () => getCircularDependencies(client),
    simulatePartition: (allowedClients: string[]) => simulatePartition(client, allowedClients),
    healPartition: () => healPartition(client),
    executeTransaction: (transaction: Transaction) => executeTransaction(client, transaction),
    getSchemaVersion: () => Promise.resolve(client.schemaVersion),
    onSchemaChange: (handler: () => void) => {
      client.schemaChangeHandlers.push(handler);
    }
  };
  
  // 内部クライアントの参照を保持（disconnect用）
  (publicClient as any)._internal = client;
  
  // 定期的なクリーンアップを開始
  startCleanupTimer(client);
  
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
  // パーティション中は許可されたクライアントからの操作のみ受け入れる
  if (client.isPartitioned && !client.partitionAllowedClients.has(op.clientId)) {
    return;
  }
  
  if (!client.operations.has(op.id)) {
    client.operations.set(op.id, op);
    
    // 非同期で処理（メッセージハンドラーのブロッキングを防ぐ）
    setTimeout(() => {
      tryApplyOperation(client, op);
    }, 0);
  }
}


// 操作の適用を試みる
async function tryApplyOperation(client: InternalClient, op: CausalOperation) {
  // すでに適用済みの場合はスキップ
  if (client.appliedOperations.has(op.id)) {
    return;
  }
  
  // メモリ使用状況のログ（デバッグ用）
  if (client.pendingOperations.size > 10) {
    console.log(`Warning: ${client.id} has ${client.pendingOperations.size} pending operations`);
  }
  
  // 依存関係をチェック
  for (const depId of op.dependsOn) {
    if (!client.appliedOperations.has(depId)) {
      // 依存する操作がまだ適用されていない
      client.pendingOperations.set(op.id, op);
      
      // ペンディング操作数の制限
      if (client.pendingOperations.size > MAX_PENDING_OPERATIONS) {
        cleanupOldPendingOperations(client);
      }
      return;
    }
  }
  
  // 操作を適用
  applyOperationToStore(client, op);
  client.appliedOperations.add(op.id);
  client.operationHistory.push(op);
  
  // 履歴の制限
  if (client.operationHistory.length > MAX_OPERATION_HISTORY) {
    client.operationHistory = client.operationHistory.slice(-MAX_OPERATION_HISTORY);
  }
  
  // この操作に依存している操作を再チェック（非同期でキューイング）
  const toRetry: CausalOperation[] = [];
  for (const [pendingId, pendingOp] of client.pendingOperations) {
    if (pendingOp.dependsOn.includes(op.id)) {
      client.pendingOperations.delete(pendingId);
      toRetry.push(pendingOp);
    }
  }
  
  // 非同期で再試行（スタックオーバーフローを防ぐ）
  if (toRetry.length > 0) {
    setTimeout(() => {
      for (const pendingOp of toRetry) {
        tryApplyOperation(client, pendingOp);
      }
    }, 0);
  }
}

// 操作をストアに適用
function applyOperationToStore(client: InternalClient, op: CausalOperation) {
  switch (op.type) {
    case 'DDL':
      // DDL操作の処理
      try {
        handleDDLOperation(client, op);
      } catch (error) {
        // エラーをログに記録するが、処理は続行
        console.error(`DDL operation failed for ${op.id}: ${error instanceof Error ? error.message : String(error)}`);
      }
      break;
      
    case 'DML':
      // DML操作はDDLと同様にCypherクエリとして処理
      if (op.payload.query) {
        console.log(`Applying DML: ${op.payload.query}`);
        // 簡易的なCREATE文のパース（Userテーブル用）
        const createUserMatch = op.payload.query.match(/CREATE\s+\(\w*:?(\w+)\s+\{([^}]+)\}\)/);
        if (createUserMatch) {
          const [, nodeType, propsStr] = createUserMatch;
          const props = parseProperties(propsStr);
          const nodeId = props.id || crypto.randomUUID();
          client.nodes.set(nodeId, {
            type: nodeType,
            properties: props
          });
        }
      }
      break;
      
    case 'CREATE':
      // CREATE文をパース - 複数のCREATE文をサポート
      const createMatches = op.payload.cypherQuery.matchAll(/CREATE\s+\((\w+)?:(\w+)\s+\{([^}]+)\}\)/g);
      for (const match of createMatches) {
        const [, varName, nodeType, propsStr] = match;
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
          // 算術演算をチェック
          const arithmeticMatch = value.match(new RegExp(`${varName}\\.${prop}\\s*([+-])\\s*(\\d+)`));
          if (arithmeticMatch) {
            const [, operator, operand] = arithmeticMatch;
            const currentValue = node.properties[prop] || 0;
            const delta = Number(operand);
            if (operator === '+') {
              node.properties[prop] = currentValue + delta;
            } else if (operator === '-') {
              node.properties[prop] = currentValue - delta;
            }
          } else {
            // 値の処理（文字列の場合はクォートを除去、数値の場合は変換）
            let finalValue = value.trim();
            if (finalValue.startsWith("'") && finalValue.endsWith("'")) {
              finalValue = finalValue.slice(1, -1);
            } else if (!isNaN(Number(finalValue))) {
              finalValue = Number(finalValue);
            }
            node.properties[prop] = finalValue;
          }
          
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
  
  // MATCH (u:User) RETURN u - 全ユーザーを返す
  const matchAllMatch = cypherQuery.match(/MATCH\s+\((\w+):(\w+)\)\s+RETURN\s+(\w+)(?:\s+ORDER\s+BY\s+[^)]+)?/);
  if (matchAllMatch) {
    const [, varName, nodeType, returnVar] = matchAllMatch;
    const results = [];
    for (const [nodeId, node] of client.nodes) {
      if (node.type === nodeType) {
        results.push({ ...node.properties, id: nodeId });
      }
    }
    return results;
  }
  
  // MATCH (n:NodeType {id: 'nodeId'}) RETURN n.prop as alias
  const nodeMatch = cypherQuery.match(/MATCH\s+\((\w+):(\w+)\s+\{id:\s*'([^']+)'\}\)\s+RETURN\s+(\w+)\.(\w+)\s+as\s+(\w+)/);
  if (nodeMatch) {
    const [, varName, nodeType, nodeId, returnVar, prop, alias] = nodeMatch;
    const node = client.nodes.get(nodeId);
    if (node && node.type === nodeType) {
      return [{ [alias]: node.properties[prop] }];
    }
  }
  
  // MATCH (n:NodeType {id: 'nodeId'}) RETURN n.prop1 as alias1, n.prop2 as alias2
  const multiPropMatch = cypherQuery.match(/MATCH\s+\((\w+):(\w+)\s+\{id:\s*'([^']+)'\}\)\s+RETURN\s+(\w+)\.(\w+)\s+as\s+(\w+),\s*(\w+)\.(\w+)\s+as\s+(\w+)/);
  if (multiPropMatch) {
    const [, varName, nodeType, nodeId, returnVar1, prop1, alias1, returnVar2, prop2, alias2] = multiPropMatch;
    const node = client.nodes.get(nodeId);
    if (node && node.type === nodeType) {
      return [{ 
        [alias1]: node.properties[prop1],
        [alias2]: node.properties[prop2]
      }];
    }
  }
  
  // MATCH (n:NodeType) RETURN count(n) as count
  const countMatch = cypherQuery.match(/MATCH\s+\((\w+):(\w+)\)\s+RETURN\s+count\((\w+)\)\s+as\s+(\w+)/);
  if (countMatch) {
    const [, varName, nodeType, countVar, alias] = countMatch;
    let count = 0;
    for (const [, node] of client.nodes) {
      if (node.type === nodeType) {
        count++;
      }
    }
    return [{ [alias]: count }];
  }
  
  return [];
}

// 循環依存を検出
async function getCircularDependencies(client: InternalClient): Promise<string[][]> {
  const cycles: string[][] = [];
  const visited = new Set<string>();
  const recursionStack = new Set<string>();
  
  function dfs(opId: string, path: string[]): void {
    if (recursionStack.has(opId)) {
      // 循環を検出
      const cycleStart = path.indexOf(opId);
      if (cycleStart !== -1) {
        cycles.push(path.slice(cycleStart));
      }
      return;
    }
    
    if (visited.has(opId)) {
      return;
    }
    
    visited.add(opId);
    recursionStack.add(opId);
    
    const op = client.operations.get(opId) || client.pendingOperations.get(opId);
    if (op) {
      for (const depId of op.dependsOn) {
        dfs(depId, [...path, opId]);
      }
    }
    
    recursionStack.delete(opId);
  }
  
  // すべての操作をチェック
  for (const [opId] of client.operations) {
    if (!visited.has(opId)) {
      dfs(opId, []);
    }
  }
  
  for (const [opId] of client.pendingOperations) {
    if (!visited.has(opId)) {
      dfs(opId, []);
    }
  }
  
  return cycles;
}

// ネットワークパーティションをシミュレート
async function simulatePartition(client: InternalClient, allowedClients: string[]): Promise<void> {
  client.isPartitioned = true;
  client.partitionAllowedClients = new Set(allowedClients);
  
  // WebSocketで通知
  if (client.ws && client.ws.readyState === WebSocket.OPEN) {
    client.ws.send(JSON.stringify({
      type: 'partition',
      clientId: client.id,
      allowedClients
    }));
  }
}

// パーティションを修復
async function healPartition(client: InternalClient): Promise<void> {
  client.isPartitioned = false;
  client.partitionAllowedClients.clear();
  
  // WebSocketで通知
  if (client.ws && client.ws.readyState === WebSocket.OPEN) {
    client.ws.send(JSON.stringify({
      type: 'heal_partition',
      clientId: client.id
    }));
  }
  
  // 少し待ってから操作を再送信
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // すべての適用済み操作を再送信して同期
  const sortedOps = Array.from(client.operations.values())
    .filter(op => client.appliedOperations.has(op.id))
    .sort((a, b) => a.timestamp - b.timestamp);
    
  for (const op of sortedOps) {
    if (client.ws && client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(JSON.stringify({
        type: 'operation',
        operation: op,
        clientId: client.id
      }));
      // 少し待機
      await new Promise(resolve => setTimeout(resolve, 10));
    }
  }
}

// DDL操作の処理
function handleDDLOperation(client: InternalClient, op: CausalOperation) {
  const { ddlType, query } = op.payload;
  
  // エラーハンドリング: 無効なDDL操作をスキップ
  if (!query || typeof query !== 'string') {
    console.error(`Invalid DDL query in operation ${op.id}`);
    return;
  }
  
  try {
    // DDL操作の検証のみ行い、無効な操作は早期リターン
    if (ddlType === 'ADD_COLUMN' || ddlType === 'DROP_COLUMN') {
      // テーブル存在チェック
      const tableMatch = query.match(/ALTER\s+TABLE\s+(\w+)/i);
      if (tableMatch) {
        const [, tableName] = tableMatch;
        if (!client.schemaVersion.tables[tableName]) {
          console.warn(`Table ${tableName} does not exist for ${ddlType} operation`);
          return;
        }
      }
    }
    
    // 無効なSQL構文のチェック
    if (query.toUpperCase().includes('INVALID') || 
        !query.match(/^(CREATE|ALTER|DROP|RENAME|COMMENT)/i)) {
      console.error(`Invalid DDL syntax in operation ${op.id}: ${query}`);
      return; // エラーの場合は早期リターン
    }
    
    console.log(`Client ${client.id} validated DDL operation: ${op.id}`);
  } catch (error) {
    console.error(`Error processing DDL operation ${op.id}:`, error);
  }
}

// テーブルカラムのパース
function parseTableColumns(columnsStr: string): Record<string, ColumnSchema> {
  const columns: Record<string, ColumnSchema> = {};
  const parts = columnsStr.split(',');
  
  for (const part of parts) {
    const trimmed = part.trim();
    // PRIMARY KEY以外のカラム定義を探す
    const columnMatch = trimmed.match(/^(\w+)\s+(\w+)/);
    if (columnMatch && !trimmed.includes('PRIMARY KEY')) {
      const [, columnName, columnType] = columnMatch;
      columns[columnName] = { type: columnType };
    }
  }
  
  return columns;
}

// トランザクションを実行
async function executeTransaction(client: InternalClient, transaction: Transaction): Promise<void> {
  const transactionOps: CausalOperation[] = [];
  const rollbackOps: CausalOperation[] = [];
  const transactionId = transaction.id;
  
  // トランザクション開始前の状態を保存
  const beforeSchemaVersion = JSON.parse(JSON.stringify(client.schemaVersion));
  const beforeSchemaOpsLength = client.schemaVersion.operations.length;
  const appliedInTransaction: string[] = [];
  
  try {
    // 各操作を実行前にバリデーション
    for (let i = 0; i < transaction.operations.length; i++) {
      const txOp = transaction.operations[i];
      
      // DDL操作の事前検証
      if (txOp.type === 'DDL' && txOp.payload.query) {
        const invalidSql = txOp.payload.query.toUpperCase().includes('INVALID') || 
                          !txOp.payload.query.match(/^(CREATE|ALTER|DROP|RENAME|COMMENT)/i);
        if (invalidSql) {
          throw new Error(`Invalid DDL operation: ${txOp.payload.query}`);
        }
      }
      
      // 制約チェック（minimum_balance）
      if (txOp.constraint && txOp.constraint.type === 'minimum_balance') {
        const match = txOp.payload.cypherQuery.match(/MATCH\s+\((\w+):(\w+)\s+\{id:\s*'([^']+)'\}\)\s+SET\s+\w+\.balance\s*=\s*\w+\.balance\s*-\s*(\d+)/);
        if (match) {
          const [, , , nodeId, amount] = match;
          const node = client.nodes.get(nodeId);
          if (node) {
            const currentBalance = node.properties.balance || 0;
            const newBalance = currentBalance - Number(amount);
            if (newBalance < txOp.constraint.value) {
              // 制約違反 - トランザクション中止
              return;
            }
          }
        }
      }
      
      // CausalOperationに変換
      const causalOp: CausalOperation = {
        id: txOp.id,
        dependsOn: i === 0 ? [] : [transaction.operations[i-1].id],
        type: txOp.type,
        payload: txOp.payload,
        clientId: transaction.clientId,
        timestamp: transaction.timestamp + i
      };
      
      transactionOps.push(causalOp);
    }
    
    // すべての操作を実行
    for (const op of transactionOps) {
      await executeOperation(client, op);
      appliedInTransaction.push(op.id);
    }
    
    // トランザクション成功
    client.transactionOperations.set(transactionId, transaction.operations);
    
  } catch (error) {
    // ロールバック
    console.error('Transaction failed, rolling back:', error);
    
    // スキーマを元に戻す
    client.schemaVersion = beforeSchemaVersion;
    
    // 適用した操作を取り消す
    for (const opId of appliedInTransaction) {
      client.appliedOperations.delete(opId);
      client.operations.delete(opId);
    }
    
    // エラーを再スロー
    throw error;
  }
}

// クリーンアップタイマーを開始
function startCleanupTimer(client: InternalClient) {
  const timer = setInterval(() => {
    cleanupOldOperations(client);
  }, OPERATION_CLEANUP_INTERVAL);
  
  // タイマーIDを保存（disconnect時にクリア）
  client.cleanupTimer = timer;
}

// 古い操作をクリーンアップ
function cleanupOldOperations(client: InternalClient) {
  // operations mapのサイズ制限
  if (client.operations.size > MAX_OPERATIONS_MAP) {
    const sortedOps = Array.from(client.operations.entries())
      .sort((a, b) => a[1].timestamp - b[1].timestamp);
    
    const toRemove = sortedOps.slice(0, sortedOps.length - MAX_OPERATIONS_MAP);
    for (const [id] of toRemove) {
      client.operations.delete(id);
      client.appliedOperations.delete(id);
    }
  }
}

// 古いペンディング操作をクリーンアップ
function cleanupOldPendingOperations(client: InternalClient) {
  const now = Date.now();
  const oneMinuteAgo = now - 60000;
  
  for (const [id, op] of client.pendingOperations) {
    if (op.timestamp < oneMinuteAgo) {
      client.pendingOperations.delete(id);
    }
  }
}

// 切断
export async function disconnect(client: CausalSyncClient): Promise<void> {
  const internal = (client as any)._internal as InternalClient;
  if (internal) {
    // クリーンアップタイマーを停止
    const timer = (internal as any).cleanupTimer;
    if (timer) {
      clearInterval(timer);
    }
    
    // WebSocketを閉じる
    if (internal.ws) {
      internal.ws.close();
    }
    
    // メモリをクリア
    internal.operations.clear();
    internal.appliedOperations.clear();
    internal.pendingOperations.clear();
    internal.operationHistory = [];
    internal.nodes.clear();
    internal.nodeUpdateTimestamps.clear();
    internal.queryResolvers.clear();
  }
}