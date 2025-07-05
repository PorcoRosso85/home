/**
 * History Sync E2E Test - TDD Red Phase
 * 履歴同期のE2Eテスト仕様
 * 
 * 規約準拠:
 * - ESモジュールのみ使用
 * - 実ブラウザでの動作確認
 * - モックフリー実装
 */

import { test, expect, waitForKuzuDBInit, waitForWebSocketConnect, createUser, waitForUserInList, getUserList } from './test-fixtures';

test.describe('履歴同期E2Eテスト', () => {
  test('新規ブラウザは過去のユーザーを取得する', async ({ browser, servers }) => {
    // 既存ブラウザでユーザー作成
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    
    await page1.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page1);
    await waitForWebSocketConnect(page1);
    
    // 過去のユーザーを作成
    const historicalUsers = [
      'Historical Alice',
      'Historical Bob',
      'Historical Charlie'
    ];
    
    for (const userName of historicalUsers) {
      await createUser(page1, userName);
      await page1.waitForTimeout(100); // 各作成を待つ
    }
    
    // 既存ブラウザのユーザーリストを確認
    const users1Before = await getUserList(page1);
    expect(users1Before.length).toBe(3);
    
    // 新規ブラウザを開く
    const context2 = await browser.newContext();
    const page2 = await context2.newPage();
    
    await page2.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page2);
    await waitForWebSocketConnect(page2);
    
    // 新規ブラウザは接続時に履歴を自動取得すべき
    await page2.waitForFunction(
      () => {
        const users = document.getElementById('users')?.textContent || '';
        return users.includes('Historical Alice') && 
               users.includes('Historical Bob') && 
               users.includes('Historical Charlie');
      },
      { timeout: 5000 }
    );
    
    // 両ブラウザのデータが一致
    const users1 = await getUserList(page1);
    const users2 = await getUserList(page2);
    
    expect(users2.sort()).toEqual(users1.sort());
    expect(users2.length).toBe(3);
    
    await context1.close();
    await context2.close();
  });
  
  test('履歴取得後もリアルタイム同期が継続する', async ({ browser, servers }) => {
    // Browser1: 既存ユーザー作成
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    
    await page1.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page1);
    await waitForWebSocketConnect(page1);
    
    await createUser(page1, 'Past User 1');
    await createUser(page1, 'Past User 2');
    
    // Browser2: 新規接続（履歴取得）
    const context2 = await browser.newContext();
    const page2 = await context2.newPage();
    
    await page2.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page2);
    await waitForWebSocketConnect(page2);
    
    // 履歴取得を待つ
    await waitForUserInList(page2, 'Past User 1');
    await waitForUserInList(page2, 'Past User 2');
    
    // Browser1: リアルタイムで新規ユーザー作成
    await createUser(page1, 'Realtime User');
    
    // Browser2: リアルタイム同期を確認
    await waitForUserInList(page2, 'Realtime User');
    
    // 全データが両ブラウザで一致
    const users1 = await getUserList(page1);
    const users2 = await getUserList(page2);
    
    expect(users1.sort()).toEqual(users2.sort());
    expect(users1).toContain('Past User 1');
    expect(users1).toContain('Past User 2');
    expect(users1).toContain('Realtime User');
    
    await context1.close();
    await context2.close();
  });
  
  test('複数の新規ブラウザが同じ履歴を取得する', async ({ browser, servers }) => {
    // Browser1: データ作成
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    
    await page1.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page1);
    await waitForWebSocketConnect(page1);
    
    const baseUsers = ['Base User A', 'Base User B', 'Base User C'];
    for (const user of baseUsers) {
      await createUser(page1, user);
    }
    
    // Browser2,3: 新規接続
    const context2 = await browser.newContext();
    const context3 = await browser.newContext();
    const page2 = await context2.newPage();
    const page3 = await context3.newPage();
    
    // 両方のブラウザを同時に開く
    await Promise.all([
      page2.goto('http://localhost:3000/demo.html'),
      page3.goto('http://localhost:3000/demo.html')
    ]);
    
    await Promise.all([
      waitForKuzuDBInit(page2),
      waitForKuzuDBInit(page3),
      waitForWebSocketConnect(page2),
      waitForWebSocketConnect(page3)
    ]);
    
    // 両方のブラウザで履歴を確認
    for (const user of baseUsers) {
      await Promise.all([
        waitForUserInList(page2, user),
        waitForUserInList(page3, user)
      ]);
    }
    
    // 全ブラウザでデータが一致
    const users1 = await getUserList(page1);
    const users2 = await getUserList(page2);
    const users3 = await getUserList(page3);
    
    expect(users2.sort()).toEqual(users1.sort());
    expect(users3.sort()).toEqual(users1.sort());
    
    await context1.close();
    await context2.close();
    await context3.close();
  });
  
  test('大量データの履歴同期', async ({ browser, servers }) => {
    test.slow(); // タイムアウトを延長
    
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    
    await page1.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page1);
    await waitForWebSocketConnect(page1);
    
    // 50ユーザーを作成
    const userCount = 50;
    console.log(`Creating ${userCount} users...`);
    
    for (let i = 0; i < userCount; i++) {
      await page1.evaluate((index) => {
        const input = document.getElementById('userName') as HTMLInputElement;
        const button = document.getElementById('createCustom') as HTMLButtonElement;
        input.value = `Bulk User ${index}`;
        button.click();
      }, i);
      
      // バッチ処理のため少し待つ
      if (i % 10 === 9) {
        await page1.waitForTimeout(500);
      }
    }
    
    // 最後のユーザーが表示されるまで待つ
    await waitForUserInList(page1, `Bulk User ${userCount - 1}`);
    
    // 新規ブラウザ
    const context2 = await browser.newContext();
    const page2 = await context2.newPage();
    
    await page2.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page2);
    await waitForWebSocketConnect(page2);
    
    // 履歴取得を確認（最初と最後のユーザー）
    await waitForUserInList(page2, 'Bulk User 0');
    await waitForUserInList(page2, `Bulk User ${userCount - 1}`);
    
    // ユーザー数を確認
    const users2 = await getUserList(page2);
    expect(users2.length).toBe(userCount);
    
    await context1.close();
    await context2.close();
  });
  
  test('履歴取得のエラー処理', async ({ browser, servers, page }) => {
    await page.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page);
    await waitForWebSocketConnect(page);
    
    // エラーログを監視
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // 不正な履歴リクエストを送信
    await page.evaluate(() => {
      const client = (window as any).client;
      if (client?.ws?.readyState === WebSocket.OPEN) {
        client.ws.send(JSON.stringify({
          type: 'requestHistory',
          fromPosition: -1, // 不正な位置
          limit: -1 // 不正な制限
        }));
      }
    });
    
    // エラーが適切に処理される
    await page.waitForTimeout(1000);
    
    // 通常動作は継続
    const testUser = `Error Test User ${Date.now()}`;
    await createUser(page, testUser);
    await waitForUserInList(page, testUser);
    
    const users = await getUserList(page);
    expect(users).toContain(testUser);
  });
});

test.describe('履歴同期のパフォーマンス', () => {
  test.skip('1000件の履歴を効率的に取得', async ({ browser, servers }) => {
    // TODO: 大規模データでのパフォーマンステスト
    // - ページング実装後にテスト
    // - 転送時間の測定
    // - メモリ使用量の確認
  });
  
  test.skip('履歴圧縮の効果測定', async ({ browser, servers }) => {
    // TODO: 圧縮機能実装後にテスト
    // - 同一エンティティへの複数更新
    // - 圧縮率の確認
    // - 最終状態の正確性
  });
});