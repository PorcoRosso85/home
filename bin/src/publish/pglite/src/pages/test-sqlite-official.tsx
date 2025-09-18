export default function TestSQLiteOfficialPage() {
  return (
    <div style={{ padding: '24px', fontFamily: 'monospace' }}>
      <h1>Official SQLite WASM Test</h1>
      
      <div id="status" style={{
        padding: '10px',
        margin: '10px 0',
        borderRadius: '4px',
        background: '#d1ecf1',
        color: '#0c5460'
      }}>
        Initializing...
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={() => (window as any).testBasicSQLite?.()}
          style={{ padding: '10px 20px', margin: '5px', cursor: 'pointer' }}
        >
          Test Basic SQLite
        </button>
        <button 
          onClick={() => (window as any).testMemoryDB?.()}
          style={{ padding: '10px 20px', margin: '5px', cursor: 'pointer' }}
        >
          Test Memory DB
        </button>
        <button 
          onClick={() => (window as any).testR2Database?.()}
          style={{ padding: '10px 20px', margin: '5px', cursor: 'pointer' }}
        >
          Test R2 Database Load
        </button>
      </div>
      
      <pre id="log" style={{
        background: '#f5f5f5',
        padding: '10px',
        whiteSpace: 'pre-wrap',
        border: '1px solid #ddd'
      }} />
      
      <script dangerouslySetInnerHTML={{ __html: `
        let sqlite3 = null;
        const log = (msg) => {
          const logEl = document.getElementById('log');
          if (logEl) logEl.textContent += msg + '\\n';
          console.log(msg);
        };

        const setStatus = (msg, type = 'info') => {
          const statusEl = document.getElementById('status');
          if (!statusEl) return;
          const colors = {
            success: { bg: '#d4edda', text: '#155724' },
            error: { bg: '#f8d7da', text: '#721c24' },
            info: { bg: '#d1ecf1', text: '#0c5460' }
          };
          const color = colors[type] || colors.info;
          statusEl.style.background = color.bg;
          statusEl.style.color = color.text;
          statusEl.textContent = msg;
        };

        async function initSQLite() {
          try {
            log('Loading sqlite3.js...');
            
            const script = document.createElement('script');
            script.src = '/wasm/sqlite3.js';
            
            await new Promise((resolve, reject) => {
              script.onload = resolve;
              script.onerror = reject;
              document.body.appendChild(script);
            });
            
            log('sqlite3.js loaded, waiting for initialization...');
            
            while (!window.sqlite3) {
              await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            log('sqlite3 object available!');
            sqlite3 = window.sqlite3;
            
            log('Initializing SQLite WASM...');
            const sqlite3Module = await sqlite3.init({
              print: log,
              printErr: (msg) => log('ERROR: ' + msg)
            });
            
            log('SQLite WASM initialized successfully!');
            log('Version: ' + sqlite3Module.version.libVersion);
            
            setStatus('SQLite WASM Ready! Version: ' + sqlite3Module.version.libVersion, 'success');
            
            window.sqlite3Module = sqlite3Module;
            return sqlite3Module;
            
          } catch (error) {
            setStatus('Failed to initialize: ' + error.message, 'error');
            log('Error: ' + error);
            throw error;
          }
        }

        window.testBasicSQLite = async function() {
          try {
            if (!window.sqlite3Module) {
              await initSQLite();
            }
            
            log('\\n=== Testing Basic SQLite ===');
            const sqlite3Module = window.sqlite3Module;
            
            log('Available APIs:');
            log('- oo1 (Object Oriented API v1): ' + !!sqlite3Module.oo1);
            log('- capi (C-style API): ' + !!sqlite3Module.capi);
            log('- wasm: ' + !!sqlite3Module.wasm);
            
            setStatus('Basic SQLite test passed!', 'success');
            
          } catch (error) {
            setStatus('Basic test failed: ' + error.message, 'error');
            log('Error: ' + error);
          }
        }

        window.testMemoryDB = async function() {
          try {
            if (!window.sqlite3Module) {
              await initSQLite();
            }
            
            log('\\n=== Testing Memory Database ===');
            const sqlite3Module = window.sqlite3Module;
            
            const db = new sqlite3Module.oo1.DB();
            log('Created new memory database');
            
            db.exec("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)");
            log('Created table: test');
            
            db.exec("INSERT INTO test (name) VALUES ('Alice'), ('Bob'), ('Charlie')");
            log('Inserted test data');
            
            const results = db.exec({
              sql: "SELECT * FROM test",
              returnValue: "resultRows",
              rowMode: "object"
            });
            
            log('Query results:');
            results.forEach(row => {
              log('  id: ' + row.id + ', name: ' + row.name);
            });
            
            db.close();
            log('Database closed');
            
            setStatus('Memory database test passed!', 'success');
            
          } catch (error) {
            setStatus('Memory DB test failed: ' + error.message, 'error');
            log('Error: ' + error);
          }
        }

        window.testR2Database = async function() {
          try {
            if (!window.sqlite3Module) {
              await initSQLite();
            }
            
            log('\\n=== Testing R2 Database Load ===');
            const sqlite3Module = window.sqlite3Module;
            
            log('Fetching test.db from R2...');
            const response = await fetch('/api/sqlite/db/test.db');
            
            if (!response.ok) {
              throw new Error('Failed to fetch: ' + response.status);
            }
            
            const buffer = await response.arrayBuffer();
            log('Database fetched: ' + buffer.byteLength + ' bytes');
            
            const p = sqlite3Module.wasm.allocFromTypedArray(buffer);
            const db = new sqlite3Module.oo1.DB();
            
            const rc = sqlite3Module.capi.sqlite3_deserialize(
              db.pointer, 'main', p, buffer.byteLength, buffer.byteLength,
              sqlite3Module.capi.SQLITE_DESERIALIZE_FREEONCLOSE
            );
            
            if (rc !== sqlite3Module.capi.SQLITE_OK) {
              throw new Error('Failed to deserialize: ' + rc);
            }
            
            log('Database loaded successfully!');
            
            const tables = db.exec({
              sql: "SELECT name FROM sqlite_master WHERE type='table'",
              returnValue: "resultRows",
              rowMode: "object"
            });
            
            log('Tables in database:');
            tables.forEach(table => {
              log('  - ' + table.name);
            });
            
            if (tables.some(t => t.name === 'users')) {
              const users = db.exec({
                sql: "SELECT * FROM users LIMIT 3",
                returnValue: "resultRows",
                rowMode: "object"
              });
              
              log('\\nSample users:');
              users.forEach(user => {
                log('  - ' + user.name + ' (' + user.email + ')');
              });
            }
            
            db.close();
            setStatus('R2 database test passed!', 'success');
            
          } catch (error) {
            setStatus('R2 DB test failed: ' + error.message, 'error');
            log('Error: ' + error);
          }
        }

        // Auto-initialize on load
        setTimeout(() => initSQLite().catch(console.error), 1000);
      ` }} />
    </div>
  );
}

export const getConfig = async () => {
  return {
    render: 'dynamic',
  };
};