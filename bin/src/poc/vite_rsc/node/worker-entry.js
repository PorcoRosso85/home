// Cloudflare Workers Entry Point for Vite RSC
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Static assets are handled by [site] configuration
    // This handler is for dynamic RSC/SSR responses
    
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Vite RSC on Cloudflare Workers</title>
          <script type="module" src="/assets/entry.browser.js"></script>
        </head>
        <body>
          <div id="root">
            <h1>Vite RSC Deployed to Cloudflare Workers</h1>
            <p>Path: ${url.pathname}</p>
            <p>Ready for RSC integration</p>
          </div>
        </body>
      </html>
    `, {
      headers: {
        'content-type': 'text/html;charset=UTF-8',
      },
    });
  },
};