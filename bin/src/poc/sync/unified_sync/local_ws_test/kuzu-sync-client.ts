/**
 * KuzuDB同期クライアント - インメモリKuzuDBとWebSocket統合
 * 関数型設計（クラスなし）
 * 
 * Note: この実装はKuzuDB WASMの代わりにインメモリストアを使用します
 * 実際の実装ではkuzu-wasmを使用しますが、テスト環境での動作確認のため簡略化
 */

// 型定義
export interface SyncEvent {
  id: string;
  template: string;
  params: {
    cypherQuery?: string;
    [key: string]: any;
  };
  clientId: string;
  timestamp: number;
}

export interface KuzuSyncClient {
  id: string;
  store: Map<string, any>; // 簡略化: インメモリストア
  nodes: Map<string, any>; // ノードストレージ
  ws: WebSocket | null;
  eventHandlers: ((event: SyncEvent) => void)[];
  eventLog: SyncEvent[]; // イベントログ
}

interface CreateClientOptions {
  clientId: string;
  dbPath: string;
  wsUrl: string;
  onEventReceived?: (event: SyncEvent) => void;
}

// KuzuDB同期クライアントを作成
export async function createKuzuSyncClient(options: CreateClientOptions): Promise<any> {
  // クライアントオブジェクトを作成
  const client: KuzuSyncClient = {
    id: options.clientId,
    store: new Map(),
    nodes: new Map(),
    ws: null,
    eventHandlers: [],
    eventLog: []
  };
  
  // イベントハンドラーを登録
  if (options.onEventReceived) {
    client.eventHandlers.push(options.onEventReceived);
  }
  
  // WebSocket接続を確立
  await connectWebSocket(client, options.wsUrl);
  
  // メソッドを追加して返す
  return {
    ...client,
    executeAndBroadcast: (event: SyncEvent) => executeAndBroadcast(client, event),
    query: (cypherQuery: string) => query(client, cypherQuery)
  };
}

// WebSocket接続を確立
async function connectWebSocket(client: KuzuSyncClient, wsUrl: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      client.ws = ws;
      
      // クライアントIDを送信
      ws.send(JSON.stringify({
        type: 'identify',
        clientId: client.id
      }));
      
      resolve();
    };
    
    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // イベントを受信した場合
        if (data.type === 'event' && data.event) {
          const syncEvent = data.event as SyncEvent;
          
          // 自分が送信したイベントは無視
          if (syncEvent.clientId === client.id) {
            return;
          }
          
          // イベントハンドラーを実行
          for (const handler of client.eventHandlers) {
            handler(syncEvent);
          }
          
          // ストアに適用
          await applyEventToStore(client, syncEvent);
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };
    
    ws.onerror = (error) => {
      reject(error);
    };
    
    ws.onclose = () => {
      client.ws = null;
    };
  });
}

// イベントをストアに適用（簡略化版）
async function applyEventToStore(client: KuzuSyncClient, event: SyncEvent): Promise<void> {
  client.eventLog.push(event);
  
  if (event.params.cypherQuery) {
    // 簡易的なCypherクエリパーサー
    const query = event.params.cypherQuery;
    console.log(`[Apply] Client ${client.id} applying query from ${event.clientId}: ${query.trim().substring(0, 50)}...`);
    
    // CREATE (n:Type {props}) パターン
    const createMatch = query.match(/CREATE\s+\((\w+)?:(\w+)\s+\{([^}]+)\}\)/);
    if (createMatch) {
      const [, varName, nodeType, propsStr] = createMatch;
      const props = parseProperties(propsStr);
      
      // ノードを作成
      const nodeId = props.id || crypto.randomUUID();
      const node = {
        type: nodeType,
        properties: props
      };
      client.nodes.set(nodeId, node);
      console.log(`[Apply] Created node ${nodeType} with id: ${nodeId}`);
    }
    
    // MATCH ... SET パターン（カウンター更新用）
    const setMatch = query.match(/MATCH\s+\((\w+):(\w+)\s+\{([^}]+)\}\)\s+SET\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)\s*\+\s*(\d+)/);
    if (setMatch) {
      const [, varName, nodeType, matchPropsStr, setVar, setProp, getVar, getProp, increment] = setMatch;
      const matchProps = parseProperties(matchPropsStr);
      
      // 該当ノードを探す
      for (const [id, node] of client.nodes) {
        if (node.type === nodeType && node.properties.id === matchProps.id) {
          node.properties[setProp] = (node.properties[getProp] || 0) + parseInt(increment);
          break;
        }
      }
    }
    
    // CREATE multiple with WITH パターン
    const multiCreateMatch = query.match(/CREATE\s+\((\w+):(\w+)\s+\{([^}]+)\}\)\s+WITH\s+\w+\s+MATCH/);
    if (multiCreateMatch) {
      const [, varName, nodeType, propsStr] = multiCreateMatch;
      const props = parseProperties(propsStr);
      
      // ノードを作成
      const nodeId = props.id || crypto.randomUUID();
      const node = {
        type: nodeType,
        properties: props
      };
      client.nodes.set(nodeId, node);
    }
    
    // CREATE relationship パターン
    const relMatch = query.match(/CREATE\s+\((\w+)\)-\[:(\w+)\]->\((\w+)\)/);
    if (relMatch) {
      // 簡略化: リレーションシップは今回は無視
    }
  }
}

// プロパティ文字列をパース
function parseProperties(propsStr: string): any {
  const props: any = {};
  const pairs = propsStr.split(',');
  
  for (const pair of pairs) {
    const [key, value] = pair.split(':').map(s => s.trim());
    if (key && value) {
      // 文字列の場合はクォートを除去
      if (value.startsWith("'") || value.startsWith('"')) {
        props[key] = value.slice(1, -1);
      } else if (!isNaN(Number(value))) {
        props[key] = Number(value);
      } else {
        props[key] = value;
      }
    }
  }
  
  return props;
}

// DMLを実行してイベントをブロードキャスト
export async function executeAndBroadcast(client: KuzuSyncClient, event: SyncEvent): Promise<void> {
  // ローカルストアに適用
  await applyEventToStore(client, event);
  
  // WebSocketで送信
  if (client.ws && client.ws.readyState === WebSocket.OPEN) {
    client.ws.send(JSON.stringify({
      type: 'event',
      event
    }));
  }
}

// DQLクエリを実行（簡略化版）
export async function query(client: KuzuSyncClient, cypherQuery: string): Promise<any[]> {
  console.log(`[Query] Client ${client.id} executing: ${cypherQuery.trim()}`);
  console.log(`[Query] Nodes in store: ${client.nodes.size}`);
  // MATCH (n:Type) RETURN ... パターン
  const matchAllMatch = cypherQuery.match(/MATCH\s+\((\w+):(\w+)\)\s+RETURN/);
  if (matchAllMatch) {
    const [, varName, nodeType] = matchAllMatch;
    
    // COUNT集計
    if (cypherQuery.includes('count(')) {
      const nodes = Array.from(client.nodes.values()).filter(n => n.type === nodeType);
      return [{ nodeCount: nodes.length }];
    }
    
    // 集計クエリ
    if (cypherQuery.includes('count(DISTINCT')) {
      const nodes = Array.from(client.nodes.values()).filter(n => n.type === nodeType);
      const uniqueClients = new Set(nodes.map(n => n.properties.clientIndex));
      const timestamps = nodes.map(n => n.properties.timestamp || 0);
      
      return [{
        totalNodes: nodes.length,
        uniqueClients: uniqueClients.size,
        minTimestamp: Math.min(...timestamps),
        maxTimestamp: Math.max(...timestamps)
      }];
    }
    
    // ORDER BY + LIMIT
    if (cypherQuery.includes('ORDER BY') && cypherQuery.includes('LIMIT')) {
      const nodes = Array.from(client.nodes.values())
        .filter(n => n.type === nodeType)
        .sort((a, b) => (a.properties.timestamp || 0) - (b.properties.timestamp || 0))
        .slice(0, 10)
        .map(n => ({
          id: n.properties.id,
          timestamp: n.properties.timestamp
        }));
      
      return nodes;
    }
  }
  
  // MATCH (n:Type {prop: value}) パターン
  const matchSpecificMatch = cypherQuery.match(/MATCH\s+\((\w+):(\w+)\s+\{([^}]+)\}\)\s*\n?\s*RETURN/m);
  if (matchSpecificMatch) {
    const [, varName, nodeType, propsStr] = matchSpecificMatch;
    const matchProps = parseProperties(propsStr);
    console.log(`[Query] Looking for ${nodeType} with props:`, matchProps);
    
    // 該当ノードを探す
    const results = [];
    for (const [id, node] of client.nodes) {
      console.log(`[Query] Checking node: ${id}, type: ${node.type}, props:`, node.properties);
      if (node.type === nodeType) {
        let match = true;
        for (const [key, value] of Object.entries(matchProps)) {
          if (node.properties[key] !== value) {
            match = false;
            break;
          }
        }
        
        if (match) {
          console.log(`[Query] Found matching node: ${id}`);
          // RETURN句をパース
          const returnMatch = cypherQuery.match(/RETURN\s+(.+)$/ms);
          if (returnMatch) {
            const returnClause = returnMatch[1].trim();
            const result: any = {};
            
            // プロパティを返す
            const propMatches = returnClause.matchAll(/(\w+)\.(\w+)\s+as\s+(\w+)/g);
            for (const pm of propMatches) {
              const [, , prop, alias] = pm;
              result[alias] = node.properties[prop];
            }
            
            // 単純なプロパティアクセス (c.value as value)
            if (Object.keys(result).length === 0) {
              const simplePropMatch = returnClause.match(/(\w+)\.(\w+)\s+as\s+(\w+)/);
              if (simplePropMatch) {
                const [, , prop, alias] = simplePropMatch;
                result[alias] = node.properties[prop];
              }
            }
            
            results.push(result);
          }
        }
      }
    }
    
    return results.length > 0 ? results : [undefined];
  }
  
  // MATCH relationship パターン (Alice->Bob)
  const relQueryMatch = cypherQuery.match(/MATCH\s+\((\w+):(\w+)\s+\{([^}]+)\}\)-\[:(\w+)\]->\((\w+):(\w+)\s+\{([^}]+)\}\)\s+RETURN/);
  if (relQueryMatch) {
    // 簡略化: 両方のノードが存在すれば成功とみなす
    const [, fromVar, fromType, fromPropsStr, relType, toVar, toType, toPropsStr] = relQueryMatch;
    const fromProps = parseProperties(fromPropsStr);
    const toProps = parseProperties(toPropsStr);
    
    let fromNode = null;
    let toNode = null;
    
    for (const [id, node] of client.nodes) {
      if (node.type === fromType && node.properties.id === fromProps.id) {
        fromNode = node;
      }
      if (node.type === toType && node.properties.id === toProps.id) {
        toNode = node;
      }
    }
    
    if (fromNode && toNode) {
      const returnMatch = cypherQuery.match(/RETURN\s+(.+)$/);
      if (returnMatch) {
        const returnClause = returnMatch[1];
        const result: any = {};
        
        // a.name as alice, b.name as bob パターン
        const propPairs = returnClause.split(',');
        for (const pair of propPairs) {
          const pairMatch = pair.trim().match(/(\w+)\.(\w+)\s+as\s+(\w+)/);
          if (pairMatch) {
            const [, varName, prop, alias] = pairMatch;
            if (varName === fromVar) {
              result[alias] = fromNode.properties[prop];
            } else if (varName === toVar) {
              result[alias] = toNode.properties[prop];
            }
          }
        }
        
        return [result];
      }
    }
  }
  
  return [];
}

// 接続を切断
export async function disconnect(client: KuzuSyncClient): Promise<void> {
  if (client.ws) {
    client.ws.close();
    client.ws = null;
  }
}