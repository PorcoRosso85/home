// Cloudflare Worker with bundled RSC and SSR handlers
// This approach manually integrates both handlers to work around the relative import issue

// Import both handlers directly
import rscHandler from './dist/rsc/index.js';
import { handleSsr } from './dist/ssr/index.js';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Serve static assets
    if (url.pathname.startsWith('/assets/')) {
      return env.ASSETS.fetch(request);
    }
    
    // Handle RSC stream requests
    if (url.pathname.endsWith('.rsc')) {
      // Use the RSC handler directly for .rsc requests
      return rscHandler(request);
    }
    
    // For HTML requests, we need to:
    // 1. Generate RSC stream
    // 2. Pass it to SSR handler
    // 3. Return HTML
    try {
      // Call RSC handler to get the stream
      const rscResponse = await rscHandler(request);
      
      // If RSC handler returns HTML (it delegates to SSR internally in production build)
      // we can return it directly
      const contentType = rscResponse.headers.get('content-type');
      if (contentType && contentType.includes('text/html')) {
        return rscResponse;
      }
      
      // Otherwise, manually call SSR handler
      // This handles the case where RSC returns a stream that needs SSR processing
      const rscStream = rscResponse.body;
      const htmlStream = await handleSsr(rscStream);
      
      return new Response(htmlStream, {
        headers: { 'content-type': 'text/html;charset=UTF-8' }
      });
      
    } catch (error) {
      console.error('Handler error:', error);
      
      // Fallback to client-side rendering
      return new Response(`<!DOCTYPE html>
<html>
<head>
  <title>Vite RSC - Fallback</title>
  <style>
    body { font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 2rem; }
    .error { background: #fef3c7; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
  </style>
</head>
<body>
  <div class="error">
    <h2>⚠️ RSC/SSR Error</h2>
    <p>Error: ${error.message}</p>
    <p>Stack: ${error.stack}</p>
    <p>Attempting client-side rendering...</p>
  </div>
  <div id="root"></div>
  <script type="module" src="/assets/index-BIf5sdHw.js"></script>
</body>
</html>`, {
        headers: { 'content-type': 'text/html;charset=UTF-8' }
      });
    }
  }
};