/**
 * KuzuDB WASM Sync Version Browser Test
 * 同期版KuzuDB WASMをブラウザで動作させる
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'http';
import { readFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Create HTTP server that serves KuzuDB sync version
async function createKuzuSyncServer() {
  const server = createServer(async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    
    if (req.url === '/') {
      res.setHeader('Content-Type', 'text/html');
      res.end(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>KuzuDB Sync Test</title>
          <script src="/kuzu-sync.js"></script>
        </head>
        <body>
          <script>
            // Global result storage
            window.testResult = { loading: true };
            
            async function runTest() {
              try {
                console.log('Starting KuzuDB sync test...');
                
                // Wait for kuzu to be available
                if (typeof kuzu === 'undefined') {
                  throw new Error('KuzuDB not loaded');
                }
                
                console.log('Initializing KuzuDB...');
                await kuzu.init();
                
                // Create database
                const db = new kuzu.Database();
                const conn = new kuzu.Connection(db);
                
                console.log('Creating schema...');
                
                // Create schema
                conn.query('CREATE NODE TABLE User(id STRING, name STRING, email STRING, PRIMARY KEY(id))');
                conn.query('CREATE NODE TABLE Post(id STRING, content STRING, PRIMARY KEY(id))');
                conn.query('CREATE REL TABLE AUTHORED(FROM User TO Post)');
                
                console.log('Inserting data...');
                
                // Insert data
                conn.query("CREATE (u:User {id: 'u1', name: 'Alice', email: 'alice@example.com'})");
                conn.query("CREATE (u:User {id: 'u2', name: 'Bob', email: 'bob@example.com'})");
                conn.query("CREATE (p:Post {id: 'p1', content: 'Hello KuzuDB'})");
                conn.query("CREATE (p:Post {id: 'p2', content: 'WASM sync works!'})");
                
                // Create relationships
                conn.query("MATCH (u:User {id: 'u1'}), (p:Post {id: 'p1'}) CREATE (u)-[:AUTHORED]->(p)");
                conn.query("MATCH (u:User {id: 'u2'}), (p:Post {id: 'p2'}) CREATE (u)-[:AUTHORED]->(p)");
                
                console.log('Querying data...');
                
                // Query users
                const userResult = conn.query('MATCH (u:User) RETURN u.id, u.name, u.email ORDER BY u.id');
                const users = userResult.getAllObjects();
                
                // Query posts with authors
                const postResult = conn.query(\`
                  MATCH (u:User)-[:AUTHORED]->(p:Post) 
                  RETURN u.name as author, p.content as content 
                  ORDER BY p.id
                \`);
                const posts = postResult.getAllObjects();
                
                // Store results
                window.testResult = {
                  loading: false,
                  success: true,
                  users: users,
                  posts: posts,
                  nodeCount: users.length,
                  edgeCount: posts.length
                };
                
                console.log('Test completed successfully');
                console.log('Users:', users);
                console.log('Posts:', posts);
                
              } catch (error) {
                console.error('Error:', error);
                window.testResult = {
                  loading: false,
                  success: false,
                  error: error.message,
                  stack: error.stack
                };
              }
            }
            
            // Run test after a short delay to ensure everything is loaded
            setTimeout(runTest, 100);
          </script>
        </body>
        </html>
      `);
    } else if (req.url === '/kuzu-sync.js') {
      // Serve the sync version
      try {
        const kuzuPath = join(__dirname, 'node_modules', 'kuzu-wasm', 'sync', 'index.js');
        const content = await readFile(kuzuPath, 'utf-8');
        res.setHeader('Content-Type', 'application/javascript');
        res.end(content);
      } catch (error) {
        console.error('Failed to load kuzu sync:', error);
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

test('test_kuzu_wasm_sync_with_graph_operations_returns_data', async () => {
  const { server, port } = await createKuzuSyncServer();
  
  try {
    const browser = await chromium.launch({
      headless: true,
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Enable console logging
    page.on('console', msg => console.log('Browser console:', msg.text()));
    page.on('pageerror', err => console.error('Browser error:', err));
    
    // Navigate to test page
    await page.goto(`http://localhost:${port}/`);
    
    // Wait for test to complete
    await page.waitForFunction(
      () => window.testResult && !window.testResult.loading,
      { timeout: 30000 }
    );
    
    // Get results
    const result = await page.evaluate(() => window.testResult);
    
    console.log('Test result:', result);
    
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