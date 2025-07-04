/**
 * KuzuDB WASM Browser Test with Proper File Serving
 * 実際のKuzuDB WASMをブラウザで動作させる
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'http';
import { readFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { createReadStream } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Create HTTP server that serves all KuzuDB files
async function createKuzuServer() {
  const server = createServer(async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    
    if (req.url === '/') {
      res.setHeader('Content-Type', 'text/html');
      res.end(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>KuzuDB WASM Test</title>
        </head>
        <body>
          <script type="module">
            import kuzu from './kuzu-wasm.js';
            
            async function runTest() {
              try {
                console.log('Initializing KuzuDB...');
                
                // Initialize KuzuDB
                await kuzu.init();
                
                // Create database
                const db = new kuzu.Database(':memory:');
                const conn = new kuzu.Connection(db);
                
                // Create schema
                await conn.query('CREATE NODE TABLE User(id STRING, name STRING, email STRING, PRIMARY KEY(id))');
                await conn.query('CREATE NODE TABLE Post(id STRING, content STRING, PRIMARY KEY(id))');
                await conn.query('CREATE REL TABLE AUTHORED(FROM User TO Post)');
                
                // Insert data
                await conn.query("CREATE (u:User {id: 'u1', name: 'Alice', email: 'alice@example.com'})");
                await conn.query("CREATE (u:User {id: 'u2', name: 'Bob', email: 'bob@example.com'})");
                await conn.query("CREATE (p:Post {id: 'p1', content: 'Hello KuzuDB'})");
                await conn.query("CREATE (p:Post {id: 'p2', content: 'WASM works!'})");
                
                // Create relationships
                await conn.query("MATCH (u:User {id: 'u1'}), (p:Post {id: 'p1'}) CREATE (u)-[:AUTHORED]->(p)");
                await conn.query("MATCH (u:User {id: 'u2'}), (p:Post {id: 'p2'}) CREATE (u)-[:AUTHORED]->(p)");
                
                // Query data
                const userResult = await conn.query('MATCH (u:User) RETURN u.id, u.name, u.email ORDER BY u.id');
                const users = userResult.getAllObjects();
                
                const postResult = await conn.query(\`
                  MATCH (u:User)-[:AUTHORED]->(p:Post) 
                  RETURN u.name as author, p.content as content 
                  ORDER BY p.id
                \`);
                const posts = postResult.getAllObjects();
                
                // Store results globally
                window.testResult = {
                  success: true,
                  users: users,
                  posts: posts,
                  nodeCount: users.length,
                  edgeCount: posts.length
                };
                
                console.log('Test completed successfully');
                
              } catch (error) {
                console.error('Error:', error);
                window.testResult = {
                  success: false,
                  error: error.message
                };
              }
            }
            
            runTest();
          </script>
        </body>
        </html>
      `);
    } else if (req.url === '/kuzu-wasm.js') {
      // Serve the ES module version
      try {
        const kuzuPath = join(__dirname, 'node_modules', 'kuzu-wasm', 'index.js');
        const content = await readFile(kuzuPath, 'utf-8');
        res.setHeader('Content-Type', 'application/javascript');
        res.end(content);
      } catch (error) {
        res.statusCode = 404;
        res.end('Not found');
      }
    } else if (req.url === '/kuzu_wasm_worker.js') {
      // Serve the worker file
      try {
        const workerPath = join(__dirname, 'node_modules', 'kuzu-wasm', 'kuzu_wasm_worker.js');
        const content = await readFile(workerPath, 'utf-8');
        res.setHeader('Content-Type', 'application/javascript');
        res.end(content);
      } catch (error) {
        res.statusCode = 404;
        res.end('Not found');
      }
    } else if (req.url.endsWith('.wasm')) {
      // Serve WASM files
      try {
        const wasmName = req.url.substring(1);
        const wasmPath = join(__dirname, 'node_modules', 'kuzu-wasm', wasmName);
        res.setHeader('Content-Type', 'application/wasm');
        createReadStream(wasmPath).pipe(res);
      } catch (error) {
        res.statusCode = 404;
        res.end('Not found');
      }
    } else {
      res.statusCode = 404;
      res.end('Not found');
    }
  });
  
  await new Promise(resolve => server.listen(0, resolve));
  const port = server.address().port;
  return { server, port };
}

test('test_real_kuzu_wasm_in_browser_returns_graph_data', async () => {
  const { server, port } = await createKuzuServer();
  
  try {
    const browser = await chromium.launch({
      headless: true,
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Enable console logging
    page.on('console', msg => console.log('Browser:', msg.text()));
    page.on('pageerror', err => console.error('Page error:', err));
    
    // Navigate to test page
    await page.goto(`http://localhost:${port}/`);
    
    // Wait for test to complete
    await page.waitForFunction(
      () => window.testResult !== undefined,
      { timeout: 30000 }
    );
    
    // Get results
    const result = await page.evaluate(() => window.testResult);
    
    // Verify results
    assert.equal(result.success, true, `Test should succeed, got error: ${result.error}`);
    assert.equal(result.users.length, 2);
    assert.equal(result.users[0]['u.name'], 'Alice');
    assert.equal(result.users[1]['u.name'], 'Bob');
    assert.equal(result.posts.length, 2);
    assert.equal(result.posts[0].author, 'Alice');
    assert.equal(result.posts[0].content, 'Hello KuzuDB');
    
    await browser.close();
    
  } finally {
    server.close();
  }
});