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
  await client1.connect('ws://localhost:8081');
  console.log('✅ Client1 connected');
  
  // クライアント2を作成
  const client2 = new SyncClient('test-client-2');
  await client2.connect('ws://localhost:8081');
  console.log('✅ Client2 connected');
  
  // Client2でメッセージ受信を監視
  const receivedMessages: any[] = [];
  // eventHandlersに直接追加
  (client2 as any).eventHandlers.push((msg: any) => {
    console.log('📨 Client2 received:', msg);
    receivedMessages.push(msg);
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
  await client3.connect('ws://localhost:8081');
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

// メイン実行
if (import.meta.main) {
  try {
    await testMultiClientSync();
    Deno.exit(0); // 成功時は明示的に終了
  } catch (error) {
    console.error('❌ Test failed:', error);
    Deno.exit(1); // エラー時は終了コード1
  }
}