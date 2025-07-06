/**
 * 最小限のWebSocketクライアントテスト
 */

import { SyncClient } from './websocket-client.ts';

async function testMinimal() {
  console.log('🧪 Minimal WebSocket Test');
  
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
  (client2 as any).eventHandlers.push((msg: any) => {
    console.log('📨 Client2 received event');
    receivedMessages.push(msg);
  });
  
  // Client1からイベント送信
  await client1.sendEvent({
    id: crypto.randomUUID(),
    template: 'CREATE_USER',
    params: { id: 'test1', name: 'Test User 1' },
    clientId: 'test-client-1',
    timestamp: Date.now()
  });
  console.log('📤 Client1 sent event');
  
  // 受信を待つ
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 検証
  if (receivedMessages.length > 0) {
    console.log('✅ Test PASSED: Broadcast working');
  } else {
    console.log('❌ Test FAILED: No message received');
    throw new Error('Broadcast failed');
  }
  
  // クリーンアップ
  client1.disconnect();
  client2.disconnect();
  
  console.log('✅ Test completed successfully');
}

// メイン実行
if (import.meta.main) {
  try {
    await testMinimal();
    Deno.exit(0);
  } catch (error) {
    console.error('❌ Test error:', error.message);
    Deno.exit(1);
  }
}