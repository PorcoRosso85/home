// Cloudflare Worker entry point for Vite RSC
// Using the official RSC handler from dist/rsc/index.js

// Import the RSC handler built by @vitejs/plugin-rsc
import rscHandler from './dist/rsc/index.js';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Serve static assets
    if (url.pathname.startsWith('/assets/')) {
      return env.ASSETS.fetch(request);
    }
    
    // Use the official RSC handler for all other requests
    // The RSC handler will:
    // 1. Generate RSC stream from server components
    // 2. Handle .rsc requests for direct RSC stream
    // 3. Delegate to SSR for HTML rendering (but we need to handle this differently on Edge)
    try {
      return await rscHandler(request);
    } catch (error) {
      console.error('RSC handler error:', error);
      
      // Fallback to CSR mode if RSC handler fails
      return new Response(`<!DOCTYPE html>
<html>
<head>
  <title>Vite RSC - Edge Mode</title>
  <style>
    body { font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 2rem; }
    .error { background: #fee; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
  </style>
</head>
<body>
  <div class="error">
    <h2>RSC Handler Error</h2>
    <p>${error.message}</p>
    <p>Falling back to client-side rendering...</p>
  </div>
  <div id="root"></div>
  <script type="module" src="/assets/index-BIf5sdHw.js"></script>
</body>
</html>`, {
        headers: { 'content-type': 'text/html;charset=UTF-8' },
      });
    }
  },
};