// Worker entry point with R2 SQLite support
import { handleSQLiteR2Request } from './worker/sqlite-r2-handler';

interface Env {
  DATA_BUCKET: R2Bucket;
  DB?: D1Database;
  R2_PUBLIC_URL?: string;
  R2_WASM_URL?: string;
  ENABLE_WASM_FROM_R2?: string;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    // Handle SQLite R2 API routes
    if (url.pathname.startsWith('/api/sqlite/')) {
      return handleSQLiteR2Request(request, env, ctx);
    }

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Max-Age': '86400',
        }
      });
    }

    // For local development, serve from R2 if enabled
    if (env.ENABLE_WASM_FROM_R2 === 'true' && url.pathname.startsWith('/wasm/')) {
      const wasmPath = url.pathname.replace('/wasm/', 'wasm-files/');
      
      try {
        const object = await env.DATA_BUCKET.get(wasmPath);
        if (object) {
          const headers = new Headers({
            'Content-Type': 'application/wasm',
            'Cache-Control': 'public, max-age=31536000',
            'Access-Control-Allow-Origin': '*'
          });
          
          return new Response(object.body, { headers });
        }
      } catch (error) {
        console.error('Error fetching WASM from R2:', error);
      }
    }

    // Default response for other routes
    return new Response('Waku + R2 SQLite Worker', {
      headers: { 'Content-Type': 'text/plain' }
    });
  }
};