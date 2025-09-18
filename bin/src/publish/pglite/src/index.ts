import html from '../public/index.html';
import indexLocal from '../public/index-local.html';

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
        description: 'PGlite runs in browser, loaded from jsdelivr CDN or local assets'
      }, null, 2), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Serve index-local.html for local asset demo
    if (url.pathname === '/index-local.html' || url.pathname === '/local') {
      return new Response(indexLocal, {
        headers: {
          'Content-Type': 'text/html;charset=UTF-8',
          'Cache-Control': 'public, max-age=3600'
        }
      });
    }
    
    // IMPORTANT: Let Cloudflare handle static assets automatically
    // Files under /pglite/* are served directly from the public/pglite/ directory
    // The modern 'assets' configuration in wrangler.toml handles this
    
    // Only serve HTML for root and unmatched HTML routes
    // Do NOT catch all routes - let static assets pass through
    if (url.pathname === '/' || url.pathname === '/index.html') {
      return new Response(html, {
        headers: {
          'Content-Type': 'text/html;charset=UTF-8',
          'Cache-Control': 'public, max-age=3600'
        }
      });
    }
    
    // Return 404 for truly unmatched routes (not static assets)
    return new Response('Not Found', { status: 404 });
  }
};