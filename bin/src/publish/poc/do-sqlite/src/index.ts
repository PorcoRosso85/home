/**
 * Worker entry point for Durable Objects with SQLite
 */

import { SQLiteDurableObject } from './do-sqlite';

export { SQLiteDurableObject };

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    
    // Route to Durable Object
    if (url.pathname.startsWith("/do/")) {
      // Extract namespace and ID from path
      // Format: /do/{namespace}/{id}/...
      const pathParts = url.pathname.split('/').filter(Boolean);
      
      if (pathParts.length < 3) {
        return new Response("Invalid DO path format. Use /do/{namespace}/{id}/...", { 
          status: 400 
        });
      }
      
      const namespace = pathParts[1]; // "sqlite" 
      const id = pathParts[2];
      
      if (namespace !== "sqlite") {
        return new Response("Unknown namespace", { status: 404 });
      }
      
      // Get DO instance
      const doId = env.SQLITE_DO.idFromName(id);
      const stub = env.SQLITE_DO.get(doId);
      
      // Forward request to DO
      const doPath = '/' + pathParts.slice(3).join('/');
      const doUrl = new URL(doPath, request.url);
      doUrl.search = url.search;
      
      return stub.fetch(new Request(doUrl, request));
    }
    
    // Root endpoint - show usage
    if (url.pathname === "/") {
      return new Response(`
        Durable Objects SQLite POC
        
        Usage:
        GET  /do/sqlite/{id}/get?key={key}     - Get value by key
        POST /do/sqlite/{id}/set               - Set key-value (JSON body)
        GET  /do/sqlite/{id}/list?limit={n}    - List recent entries
        DELETE /do/sqlite/{id}/delete?key={key} - Delete by key
        
        Example:
        curl -X POST https://your-worker.workers.dev/do/sqlite/test/set \\
          -H "Content-Type: application/json" \\
          -d '{"key": "hello", "value": "world"}'
      `, {
        headers: { "Content-Type": "text/plain" }
      });
    }
    
    return new Response("Not found", { status: 404 });
  }
};