import html from '../public/index.html';

export interface Env {
  // Add environment bindings here if needed
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    // Health check endpoint
    if (url.pathname === '/health') {
      return new Response('OK', { status: 200 });
    }
    
    // Info endpoint
    if (url.pathname === '/info') {
      return new Response(JSON.stringify({
        name: 'pglite-inmemory-stg',
        version: '1.0.0',
        mode: 'client-side',
        pglite_version: '0.2.14',
        description: 'PGlite runs in browser, loaded from jsdelivr CDN'
      }, null, 2), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Serve the HTML page for all other routes
    return new Response(html, {
      headers: {
        'Content-Type': 'text/html;charset=UTF-8',
        'Cache-Control': 'public, max-age=3600'
      }
    });
  }
};