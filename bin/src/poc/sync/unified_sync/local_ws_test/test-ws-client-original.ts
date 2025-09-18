/**
 * WebSocketクライアントテスト（非ブラウザ環境）
 * サーバー機能の検証に特化
 */

import { SyncClient } from './websocket-client.ts';

// 複数クライアントのテスト
async function testMultiClientSync() {
  console.log('🧪 WebSocket Multi-Client Test (Non-Browser)');
  
  // クライアント1を作成
  const client1 = new SyncClient('test-client-1');
  await client1.connect('ws://localhost:8080');
  console.log('✅ Client1 connected');
  
  // クライアント2を作成
  const client2 = new SyncClient('test-client-2');
  await client2.connect('ws://localhost:8080');
  console.log('✅ Client2 connected');
  
  // Client2でメッセージ受信を監視
  const receivedMessages: any[] = [];
  // eventHandlersに直接追加
  (client2 as any).eventHandlers.push((msg: any) => {
    console.log('📨 Client2 received:', msg);
    receivedMessages.push(msg);
  });
  
  // デバッグ: WebSocketメッセージも監視
  (client2 as any).ws.addEventListener('message', (event: MessageEvent) => {
    console.log('🔍 Client2 raw message:', event.data);
  });
  
  // Client1からイベント送信（サーバーが要求するフォーマット）
  await client1.sendEvent({
    id: crypto.randomUUID(),
    template: 'CREATE_USER',
    params: { id: 'test1', name: 'Test User 1' },
    clientId: 'test-client-1',
    timestamp: Date.now()
  });
  console.log('📤 Client1 sent CREATE_USER event');
  
  // 受信を待つ
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 検証
  if (receivedMessages.length > 0) {
    console.log('✅ Broadcast working: Client2 received event from Client1');
  } else {
    console.log('❌ Broadcast failed: No message received');
  }
  
  // 履歴テスト
  console.log('\n🧪 Testing History Sync...');
  
  // Client3を作成（履歴を受信すべき）
  const client3 = new SyncClient('test-client-3');
  await client3.connect('ws://localhost:8080');
  console.log('✅ Client3 connected');
  
  // 履歴リクエスト
  const historyReceived: any[] = [];
  // historyHandlersに直接追加
  (client3 as any).historyHandlers.push((events: any[]) => {
    historyReceived.push(...events);
  });
  
  // requestHistoryFromを使用（位置0から）
  await client3.requestHistoryFrom(0);
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  if (historyReceived.length > 0) {
    console.log(`✅ History sync working: ${historyReceived.length} events received`);
  } else {
    console.log('❌ History sync failed');
  }
  
  // クリーンアップ
  client1.disconnect();
  client2.disconnect();
  client3.disconnect();
  
  console.log('\n✅ Test completed');
}

// 同時接続テスト
async function testConcurrentConnections() {
  console.log('\n🧪 Concurrent Connections Test');
  
  const clients: SyncClient[] = [];
  const clientCount = 10;
  
  // 10クライアント同時接続
  const connectionPromises = [];
  for (let i = 0; i < clientCount; i++) {
    const client = new SyncClient(`concurrent-client-${i}`);
    clients.push(client);
    connectionPromises.push(client.connect('ws://localhost:8080'));
  }
  
  await Promise.all(connectionPromises);
  console.log(`✅ ${clientCount} clients connected simultaneously`);
  
  // ブロードキャストテスト
  let receivedCount = 0;
  clients.forEach((client, index) => {
    if (index > 0) { // 最初のクライアント以外
      (client as any).eventHandlers.push(() => receivedCount++);
    }
  });
  
  // 最初のクライアントからメッセージ送信（サーバーが要求するフォーマット）
  await clients[0].sendEvent({
    id: crypto.randomUUID(),
    template: 'TEST_BROADCAST',
    params: { message: 'Hello all!' },
    clientId: 'test-client-0',
    timestamp: Date.now()
  });
  
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  console.log(`📊 Broadcast result: ${receivedCount}/${clientCount - 1} clients received message`);
  
  // クリーンアップ
  clients.forEach(client => client.disconnect());
}

// メイン実行
if (import.meta.main) {
  try {
    await testMultiClientSync();
    await testConcurrentConnections();
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}