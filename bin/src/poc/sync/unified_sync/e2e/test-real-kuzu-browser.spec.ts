/**
 * Real KuzuDB WASM Browser Test - モック一切なし
 * 実際のブラウザ環境でKuzuDB WASMを実行
 */

import { test, expect } from '@playwright/test';

test('KuzuDB WASM works in real browser without mocks', async ({ page }) => {
  // テスト用HTMLを提供
  await page.setContent(`
    <!DOCTYPE html>
    <html>
    <head>
      <script type="module">
        import kuzu from 'https://unpkg.com/kuzu-wasm@0.10.0/index.js';
        
        window.testKuzuDB = async () => {
          // 初期化
          await kuzu.init();
          
          // Database作成
          const db = new kuzu.Database(':memory:');
          const conn = new kuzu.Connection(db);
          
          // スキーマ作成
          await conn.query(\`
            CREATE NODE TABLE User(
              id STRING, 
              name STRING, 
              email STRING,
              PRIMARY KEY(id)
            )
          \`);
          
          // データ挿入
          await conn.query(\`
            CREATE (u:User {
              id: 'u1', 
              name: 'Alice',
              email: 'alice@example.com'
            })
          \`);
          
          // クエリ実行
          const result = await conn.query(\`
            MATCH (u:User)
            RETURN u.id as id, u.name as name, u.email as email
          \`);
          
          // 結果取得
          const users = await result.getAllObjects();
          
          return users;
        };
      </script>
    </head>
    <body>
      <h1>KuzuDB WASM Test</h1>
    </body>
    </html>
  `);
  
  // ブラウザでKuzuDB実行
  const users = await page.evaluate(async () => {
    return await window.testKuzuDB();
  });
  
  // 検証
  expect(users).toHaveLength(1);
  expect(users[0]).toEqual({
    id: 'u1',
    name: 'Alice',
    email: 'alice@example.com'
  });
});

test('WebSocket sync between browsers without mocks', async ({ browser }) => {
  // 実際のWebSocketサーバーが必要
  const context1 = await browser.newContext();
  const context2 = await browser.newContext();
  
  const page1 = await context1.newPage();
  const page2 = await context2.newPage();
  
  // 両方のページでKuzuDBクライアントを初期化
  const clientHTML = `
    <!DOCTYPE html>
    <html>
    <head>
      <script type="module">
        import kuzu from 'https://unpkg.com/kuzu-wasm@0.10.0/index.js';
        
        class BrowserKuzuClient {
          async initialize() {
            await kuzu.init();
            this.db = new kuzu.Database(':memory:');
            this.conn = new kuzu.Connection(this.db);
            
            await this.conn.query(\`
              CREATE NODE TABLE User(id STRING, name STRING, PRIMARY KEY(id))
            \`);
            
            // WebSocket接続
            this.ws = new WebSocket('ws://localhost:8080');
            this.ws.onmessage = async (event) => {
              const data = JSON.parse(event.data);
              if (data.type === 'sync') {
                await this.applyEvent(data.event);
              }
            };
          }
          
          async createUser(id, name) {
            await this.conn.query(\`
              CREATE (u:User {id: $id, name: $name})
            \`, { id, name });
            
            // 他のクライアントに同期
            if (this.ws.readyState === WebSocket.OPEN) {
              this.ws.send(JSON.stringify({
                type: 'sync',
                event: { template: 'CREATE_USER', params: { id, name } }
              }));
            }
          }
          
          async applyEvent(event) {
            if (event.template === 'CREATE_USER') {
              await this.conn.query(\`
                CREATE (u:User {id: $id, name: $name})
              \`, event.params);
            }
          }
          
          async getUsers() {
            const result = await this.conn.query(\`
              MATCH (u:User) RETURN u.id as id, u.name as name
            \`);
            return await result.getAllObjects();
          }
        }
        
        window.client = new BrowserKuzuClient();
        await window.client.initialize();
      </script>
    </head>
    <body><h1>KuzuDB Client</h1></body>
    </html>
  `;
  
  await page1.setContent(clientHTML);
  await page2.setContent(clientHTML);
  
  // ページ1でユーザー作成
  await page1.evaluate(async () => {
    await window.client.createUser('u1', 'Alice');
  });
  
  // 同期を待つ
  await page1.waitForTimeout(100);
  
  // ページ2で確認
  const users = await page2.evaluate(async () => {
    return await window.client.getUsers();
  });
  
  expect(users).toContainEqual({ id: 'u1', name: 'Alice' });
});