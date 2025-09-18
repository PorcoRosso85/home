// Simplified Cloudflare Worker for Vite RSC
// Serves pre-built assets without complex RSC handling

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Health check
    if (url.pathname === '/health') {
      return new Response('OK', { status: 200 });
    }
    
    // Serve static assets
    if (url.pathname.startsWith('/assets/')) {
      return env.ASSETS.fetch(request);
    }
    
    // For all other requests, serve the client-side app
    // This enables CSR mode with the built React components
    const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vite RSC on Cloudflare Workers</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
      margin: 0;
      padding: 2rem;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
    }
    #root {
      max-width: 800px;
      margin: 0 auto;
      background: white;
      padding: 2rem;
      border-radius: 12px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    .loading {
      text-align: center;
      color: #666;
      font-size: 1.2rem;
    }
  </style>
</head>
<body>
  <div id="root">
    <div class="loading">Loading Vite RSC App...</div>
  </div>
  <script type="module" src="/assets/index-BIf5sdHw.js"></script>
</body>
</html>`;
    
    return new Response(html, {
      headers: {
        'content-type': 'text/html;charset=UTF-8',
        'cache-control': 'no-cache'
      }
    });
  }
};