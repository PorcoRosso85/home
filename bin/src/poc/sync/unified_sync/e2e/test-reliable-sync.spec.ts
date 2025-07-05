/**
 * Reliable E2E Sync Test
 * 確実性を重視した完全なE2Eテスト
 * 
 * 規約準拠:
 * - ESモジュールのみ使用
 * - モックフリー実装
 * - ヘルスチェック付き
 */

import { test, expect, waitForKuzuDBInit, waitForWebSocketConnect, createUser, waitForUserInList, getUserList } from './test-fixtures';

test.describe('確実なE2E同期テスト', () => {
  test('基本同期: Browser1作成 → Browser2確認', async ({ browser, servers }) => {
    // serversフィクスチャによりサーバーは起動済み＆ヘルスチェック完了
    
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // デモページを開く
    await page1.goto('http://localhost:3000/demo.html');
    await page2.goto('http://localhost:3000/demo.html');
    
    // KuzuDB初期化を確実に待つ
    await Promise.all([
      waitForKuzuDBInit(page1),
      waitForKuzuDBInit(page2)
    ]);
    
    // WebSocket接続を確実に待つ
    await Promise.all([
      waitForWebSocketConnect(page1),
      waitForWebSocketConnect(page2)
    ]);
    
    // Browser1でユーザー作成
    const testUserName = `Test User ${Date.now()}`;
    await createUser(page1, testUserName);
    
    // Browser2で同期を確認
    await waitForUserInList(page2, testUserName);
    
    // 両方のブラウザでデータが一致することを確認
    const users1 = await getUserList(page1);
    const users2 = await getUserList(page2);
    
    expect(users1).toEqual(users2);
    expect(users1).toContain(testUserName);
    
    // クリーンアップ
    await context1.close();
    await context2.close();
  });
  
  test('双方向同期: 両ブラウザから作成', async ({ browser, servers }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    await page1.goto('http://localhost:3000/demo.html');
    await page2.goto('http://localhost:3000/demo.html');
    
    // 初期化を待つ
    await Promise.all([
      waitForKuzuDBInit(page1),
      waitForKuzuDBInit(page2),
      waitForWebSocketConnect(page1),
      waitForWebSocketConnect(page2)
    ]);
    
    // 異なるユーザーを同時に作成
    const user1 = `Alice ${Date.now()}`;
    const user2 = `Bob ${Date.now()}`;
    
    await Promise.all([
      createUser(page1, user1),
      createUser(page2, user2)
    ]);
    
    // 両方のブラウザで両方のユーザーが表示されるまで待つ
    await Promise.all([
      waitForUserInList(page1, user1),
      waitForUserInList(page1, user2),
      waitForUserInList(page2, user1),
      waitForUserInList(page2, user2)
    ]);
    
    // データの一致を確認
    const users1 = await getUserList(page1);
    const users2 = await getUserList(page2);
    
    expect(users1.sort()).toEqual(users2.sort());
    expect(users1).toContain(user1);
    expect(users1).toContain(user2);
    
    await context1.close();
    await context2.close();
  });
  
  test('再接続時の同期維持', async ({ browser, servers, page }) => {
    // 初期ブラウザでユーザー作成
    await page.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page);
    await waitForWebSocketConnect(page);
    
    const persistentUser = `Persistent User ${Date.now()}`;
    await createUser(page, persistentUser);
    
    // WebSocket切断をシミュレート
    await page.evaluate(() => {
      (window as any).client?.ws?.close();
    });
    
    // 再接続を待つ
    await page.waitForTimeout(3000); // 再接続間隔
    await waitForWebSocketConnect(page);
    
    // データが保持されていることを確認
    const users = await getUserList(page);
    expect(users).toContain(persistentUser);
    
    // 新しいブラウザでも確認
    const newContext = await browser.newContext();
    const newPage = await newContext.newPage();
    
    await newPage.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(newPage);
    await waitForWebSocketConnect(newPage);
    
    const newUsers = await getUserList(newPage);
    expect(newUsers).toContain(persistentUser);
    
    await newContext.close();
  });
  
  test('エラー処理: 不正なデータ送信', async ({ page, servers }) => {
    await page.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page);
    await waitForWebSocketConnect(page);
    
    // コンソールエラーを監視
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // 不正なイベントを送信
    await page.evaluate(() => {
      const client = (window as any).client;
      if (client?.ws?.readyState === WebSocket.OPEN) {
        // 必須フィールドなしのイベント
        client.ws.send(JSON.stringify({
          type: 'event',
          payload: {
            template: 'CREATE_USER',
            params: { name: 'Invalid' }
            // id, clientId, timestamp が欠落
          }
        }));
      }
    });
    
    // エラーレスポンスを待つ
    await page.waitForTimeout(1000);
    
    // サーバーは動作を継続していることを確認
    const validUser = `Valid User ${Date.now()}`;
    await createUser(page, validUser);
    await waitForUserInList(page, validUser);
    
    const users = await getUserList(page);
    expect(users).toContain(validUser);
  });
});

test.describe('負荷テスト', () => {
  test.skip('10ブラウザ同時接続', async ({ browser, servers }) => {
    const contexts = [];
    const pages = [];
    
    // 10個のブラウザコンテキストを作成
    for (let i = 0; i < 10; i++) {
      const context = await browser.newContext();
      const page = await context.newPage();
      
      contexts.push(context);
      pages.push(page);
      
      await page.goto('http://localhost:3000/demo.html');
    }
    
    // 全ページの初期化を待つ
    await Promise.all(pages.map(page => waitForKuzuDBInit(page)));
    await Promise.all(pages.map(page => waitForWebSocketConnect(page)));
    
    // 各ブラウザから異なるユーザーを作成
    const userNames = pages.map((_, i) => `User ${i} - ${Date.now()}`);
    
    await Promise.all(
      pages.map((page, i) => createUser(page, userNames[i]))
    );
    
    // 全ブラウザで全ユーザーが表示されることを確認
    for (const page of pages) {
      for (const userName of userNames) {
        await waitForUserInList(page, userName);
      }
    }
    
    // データの一致を確認（最初と最後のブラウザ）
    const firstUsers = await getUserList(pages[0]);
    const lastUsers = await getUserList(pages[9]);
    
    expect(firstUsers.sort()).toEqual(lastUsers.sort());
    expect(firstUsers.length).toBe(10);
    
    // クリーンアップ
    await Promise.all(contexts.map(ctx => ctx.close()));
  });
});