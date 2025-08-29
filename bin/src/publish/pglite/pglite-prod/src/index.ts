import { PGlite } from '@electric-sql/pglite';

let pg: PGlite | null = null;

interface Env {}

const PGLITE_VERSION = '0.2.14';
const CDN_BASE = `https://cdn.jsdelivr.net/npm/@electric-sql/pglite@${PGLITE_VERSION}/dist`;

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'healthy', version: PGLITE_VERSION }), {
        headers: { 'content-type': 'application/json' },
      });
    }

    // Initialize PGlite with CDN resources
    if (!pg) {
      try {
        console.log('Fetching PGlite resources from CDN...');
        const [wasmResponse, dataResponse] = await Promise.all([
          fetch(`${CDN_BASE}/postgres.wasm`),
          fetch(`${CDN_BASE}/postgres.data`)
        ]);
        
        if (!wasmResponse.ok || !dataResponse.ok) {
          throw new Error(`Failed to load resources: WASM ${wasmResponse.status}, Data ${dataResponse.status}`);
        }
        
        console.log('Compiling WASM module...');
        const [wasmBuffer, fsData] = await Promise.all([
          wasmResponse.arrayBuffer(),
          dataResponse.arrayBuffer()
        ]);
        const wasmModule = await WebAssembly.compile(wasmBuffer);
        
        console.log('Initializing PGlite...');
        pg = new PGlite({
          wasmModule,
          fsDataBinary: new Uint8Array(fsData),
        });
        console.log('PGlite initialized successfully');
      } catch (error) {
        console.error('PGlite initialization error:', error);
        return new Response(JSON.stringify({ 
          error: 'PGlite initialization failed', 
          details: error instanceof Error ? error.message : String(error),
          cdn_base: CDN_BASE
        }), {
          status: 500,
          headers: { 'content-type': 'application/json' },
        });
      }
    }

    if (url.pathname === '/query' && request.method === 'POST') {
      try {
        const { sql } = await request.json() as { sql: string };
        const result = await pg.exec(sql);
        return new Response(JSON.stringify({ success: true, result }), {
          headers: { 'content-type': 'application/json' },
        });
      } catch (error) {
        return new Response(JSON.stringify({ 
          success: false, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }), {
          status: 400,
          headers: { 'content-type': 'application/json' },
        });
      }
    }

    // Info endpoint
    if (url.pathname === '/info') {
      return new Response(JSON.stringify({
        about: 'PGlite In-Memory STG Worker',
        version: PGLITE_VERSION,
        cdn_base: CDN_BASE,
        endpoints: {
          '/': 'Demo counter (increments on each request)',
          '/health': 'Health check endpoint',
          '/info': 'This info endpoint',
          '/query': 'POST SQL queries ({"sql": "SELECT 1"})'
        }
      }, null, 2), {
        headers: { 'content-type': 'application/json' },
      });
    }

    // Default demo response
    try {
      const demoSql = `
        SELECT NOW() AS now, version() AS version;
        CREATE TABLE IF NOT EXISTS demo_counter (
          id INT PRIMARY KEY NOT NULL,
          label TEXT NOT NULL,
          count INT DEFAULT 0,
          last_updated TIMESTAMP DEFAULT NOW()
        );
        INSERT INTO demo_counter (id, label) VALUES (1, 'Page Views') ON CONFLICT DO NOTHING;
        UPDATE demo_counter SET count = count + 1, last_updated = NOW() WHERE id = 1;
        SELECT * FROM demo_counter;
      `;

      const result = await pg.exec(demoSql);
      
      return new Response(JSON.stringify({
        about: 'PGlite In-Memory STG Worker',
        environment: 'staging',
        endpoints: {
          '/': 'Demo counter (increments on each request)',
          '/health': 'Health check endpoint',
          '/info': 'Worker information',
          '/query': 'POST SQL queries ({"sql": "SELECT 1"})'
        },
        demo_result: result,
      }, null, 2), {
        headers: { 'content-type': 'application/json' },
      });
    } catch (error) {
      return new Response(JSON.stringify({ 
        error: 'Query execution failed', 
        details: error instanceof Error ? error.message : String(error) 
      }), {
        status: 500,
        headers: { 'content-type': 'application/json' },
      });
    }
  },
} satisfies ExportedHandler<Env>;