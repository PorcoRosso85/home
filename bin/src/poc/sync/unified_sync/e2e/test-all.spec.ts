/**
 * 統合E2Eテスト - 全機能の動作確認
 * nix run .#test で実行
 */

import { test, expect, waitForKuzuDBInit, waitForWebSocketConnect, createUser, waitForUserInList, getUserList } from './test-fixtures';

test.describe('KuzuDB Multi-Browser Sync', () => {
  test('完全な同期シナリオ', async ({ browser, servers }) => {
    // === Phase 1: 基本的な同期 ===
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    await page1.goto('http://localhost:3000/demo.html');
    await page2.goto('http://localhost:3000/demo.html');
    
    await Promise.all([
      waitForKuzuDBInit(page1),
      waitForKuzuDBInit(page2),
      waitForWebSocketConnect(page1),
      waitForWebSocketConnect(page2)
    ]);
    
    // Browser1でユーザー作成
    await createUser(page1, 'Alice');
    
    // Browser2で同期確認
    await waitForUserInList(page2, 'Alice');
    
    // === Phase 2: 履歴同期 ===
    // Browser1で追加ユーザー作成
    await createUser(page1, 'Bob');
    await createUser(page1, 'Charlie');
    
    // Browser3を新規接続（履歴同期テスト）
    const context3 = await browser.newContext();
    const page3 = await context3.newPage();
    
    await page3.goto('http://localhost:3000/demo.html');
    await waitForKuzuDBInit(page3);
    await waitForWebSocketConnect(page3);
    
    // 履歴からユーザーを取得
    await waitForUserInList(page3, 'Alice');
    await waitForUserInList(page3, 'Bob');
    await waitForUserInList(page3, 'Charlie');
    
    // === Phase 3: 双方向同期 ===
    // Browser2とBrowser3から同時作成
    await Promise.all([
      createUser(page2, 'David'),
      createUser(page3, 'Eve')
    ]);
    
    // 全ブラウザで全ユーザーが見える
    await Promise.all([
      waitForUserInList(page1, 'David'),
      waitForUserInList(page1, 'Eve'),
      waitForUserInList(page2, 'Eve'),
      waitForUserInList(page3, 'David')
    ]);
    
    // === 最終確認 ===
    const users1 = await getUserList(page1);
    const users2 = await getUserList(page2);
    const users3 = await getUserList(page3);
    
    // 全ブラウザでデータが完全に一致
    expect(users1.sort()).toEqual(users2.sort());
    expect(users2.sort()).toEqual(users3.sort());
    expect(users1.length).toBe(5); // Alice, Bob, Charlie, David, Eve
    
    // クリーンアップ
    await context1.close();
    await context2.close();
    await context3.close();
  });
});