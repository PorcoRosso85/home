/**
 * Multi-Browser Sync Integration Test
 * 複数ブラウザ同期の統合テスト - 完全版
 * 
 * 規約準拠:
 * - ESモジュールのみ使用
 * - モックフリー実装
 * - 実際のサーバーとブラウザを使用
 */

import { test, expect, type Page } from '@playwright/test';

// WebSocketサーバーとHTTPサーバーの起動を前提とする
test.describe('Multi-Browser KuzuDB Sync', () => {
  let wsProcess: any;
  let httpProcess: any;

  test.beforeAll(async () => {
    // WebSocketサーバー起動
    const { spawn } = await import('node:child_process');
    
    wsProcess = spawn('deno', ['run', '--allow-net', '../websocket-server.ts'], {
      cwd: __dirname,
      stdio: 'pipe'
    });
    
    // HTTPサーバー起動
    httpProcess = spawn('deno', ['run', '--allow-net', '--allow-read', '../serve.ts'], {
      cwd: __dirname,
      stdio: 'pipe'
    });
    
    // サーバー起動を待つ
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // サーバーログ出力
    wsProcess.stdout.on('data', (data: Buffer) => {
      console.log('[WS Server]:', data.toString().trim());
    });
    
    wsProcess.stderr.on('data', (data: Buffer) => {
      console.error('[WS Server Error]:', data.toString().trim());
    });
  });

  test.afterAll(async () => {
    // サーバー停止
    if (wsProcess) wsProcess.kill();
    if (httpProcess) httpProcess.kill();
  });

  test('同期: Browser1でユーザー作成 → Browser2で確認', async ({ browser }) => {
    // 2つのブラウザコンテキストを作成
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // コンソールログを監視
    const logs1: string[] = [];
    const logs2: string[] = [];
    
    page1.on('console', msg => {
      const text = msg.text();
      logs1.push(text);
      console.log('[Browser1]:', text);
    });
    
    page2.on('console', msg => {
      const text = msg.text();
      logs2.push(text);
      console.log('[Browser2]:', text);
    });
    
    // WebSocket通信を監視
    page1.on('websocket', ws => {
      console.log('[Browser1] WebSocket created:', ws.url());
      ws.on('framesent', evt => console.log('[Browser1] Sent:', evt.payload));
      ws.on('framereceived', evt => console.log('[Browser1] Received:', evt.payload));
    });
    
    page2.on('websocket', ws => {
      console.log('[Browser2] WebSocket created:', ws.url());
      ws.on('framesent', evt => console.log('[Browser2] Sent:', evt.payload));
      ws.on('framereceived', evt => console.log('[Browser2] Received:', evt.payload));
    });
    
    // 両方のページでデモページを開く
    await page1.goto('http://localhost:3000/demo.html');
    await page2.goto('http://localhost:3000/demo.html');
    
    // 初期化完了を待つ
    await page1.waitForFunction(() => {
      const log = document.getElementById('log');
      return log?.textContent?.includes('KuzuDB initialized');
    }, { timeout: 10000 });
    
    await page2.waitForFunction(() => {
      const log = document.getElementById('log');
      return log?.textContent?.includes('KuzuDB initialized');
    }, { timeout: 10000 });
    
    // Browser1でユーザー作成
    await page1.fill('#userName', 'Test User from Browser1');
    await page1.click('#createCustom');
    
    // 同期完了を待つ - Browser2でユーザーが表示されるまで
    await page2.waitForFunction(() => {
      const users = document.getElementById('users');
      return users?.textContent?.includes('Test User from Browser1');
    }, { timeout: 5000 });
    
    // Browser2でデータを確認
    const users2 = await page2.$$eval('#users .user', users => 
      users.map(u => u.textContent?.trim())
    );
    
    // 検証
    expect(users2).toContainEqual(expect.stringContaining('Test User from Browser1'));
    
    // ログ確認
    expect(logs1.some(log => log.includes('Created user'))).toBe(true);
    expect(logs2.some(log => log.includes('Synced user'))).toBe(true);
    
    // クリーンアップ
    await context1.close();
    await context2.close();
  });

  test('双方向同期: 両ブラウザから作成して相互確認', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    await page1.goto('http://localhost:3000/demo.html');
    await page2.goto('http://localhost:3000/demo.html');
    
    // 初期化完了を待つ
    await Promise.all([
      page1.waitForFunction(() => document.getElementById('log')?.textContent?.includes('WebSocket connected')),
      page2.waitForFunction(() => document.getElementById('log')?.textContent?.includes('WebSocket connected'))
    ]);
    
    // 両方から同時にユーザー作成
    await Promise.all([
      page1.evaluate(() => {
        document.getElementById('userName').value = 'Alice from Browser1';
        document.getElementById('createCustom').click();
      }),
      page2.evaluate(() => {
        document.getElementById('userName').value = 'Bob from Browser2';
        document.getElementById('createCustom').click();
      })
    ]);
    
    // 両方のブラウザで両方のユーザーが表示されるまで待つ
    await Promise.all([
      page1.waitForFunction(() => {
        const users = document.getElementById('users')?.textContent || '';
        return users.includes('Alice from Browser1') && users.includes('Bob from Browser2');
      }),
      page2.waitForFunction(() => {
        const users = document.getElementById('users')?.textContent || '';
        return users.includes('Alice from Browser1') && users.includes('Bob from Browser2');
      })
    ]);
    
    // 検証
    const users1 = await page1.$$eval('#users .user', users => users.map(u => u.textContent));
    const users2 = await page2.$$eval('#users .user', users => users.map(u => u.textContent));
    
    // 両方のブラウザで同じユーザーが表示されている
    expect(users1.length).toBe(2);
    expect(users2.length).toBe(2);
    
    await context1.close();
    await context2.close();
  });

  test('イベント履歴: 新規接続時に過去のイベントを取得', async ({ browser }) => {
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    
    await page1.goto('http://localhost:3000/demo.html');
    await page1.waitForFunction(() => document.getElementById('log')?.textContent?.includes('KuzuDB initialized'));
    
    // 複数のユーザーを作成
    const userNames = ['Historical User 1', 'Historical User 2', 'Historical User 3'];
    
    for (const name of userNames) {
      await page1.fill('#userName', name);
      await page1.click('#createCustom');
      await page1.waitForTimeout(100); // 各作成を待つ
    }
    
    // 新しいブラウザを開く
    const context2 = await browser.newContext();
    const page2 = await context2.newPage();
    
    await page2.goto('http://localhost:3000/demo.html');
    
    // TODO: 履歴取得機能が実装されたら、ここで検証
    // 現在のdemo.htmlには履歴取得機能がないため、
    // 新規接続時の初期同期は実装されていない
    
    await context1.close();
    await context2.close();
  });

  test('エラーハンドリング: 不正なイベントを送信', async ({ page }) => {
    await page.goto('http://localhost:3000/demo.html');
    await page.waitForFunction(() => document.getElementById('log')?.textContent?.includes('WebSocket connected'));
    
    // 不正なイベントを送信
    const errorReceived = await page.evaluate(async () => {
      const client = (window as any).client;
      
      try {
        // WebSocketを直接操作して不正なイベントを送信
        client.ws.send(JSON.stringify({
          type: 'event',
          payload: {
            // id なし（必須フィールド）
            template: 'CREATE_USER',
            params: { name: 'Invalid' }
          }
        }));
        
        // エラーレスポンスを待つ
        return new Promise((resolve) => {
          const originalOnMessage = client.ws.onmessage;
          client.ws.onmessage = (event: MessageEvent) => {
            const data = JSON.parse(event.data);
            if (data.type === 'error') {
              resolve(data.error);
            }
            originalOnMessage?.call(client.ws, event);
          };
          
          setTimeout(() => resolve(null), 1000);
        });
      } catch (error) {
        return error.message;
      }
    });
    
    // エラーメッセージを確認
    expect(errorReceived).toContain('Invalid event');
  });
});