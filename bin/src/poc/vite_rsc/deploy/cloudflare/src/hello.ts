export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    
    // Serve client JavaScript
    if (url.pathname === '/client.js') {
      // In production, this would be served from dist/client/index.js
      const clientJs = `
        console.log('Client JS loaded! 🎉');
        document.addEventListener('DOMContentLoaded', () => {
          const clientDiv = document.getElementById('client-message');
          if (clientDiv) {
            clientDiv.textContent = 'Client-side JavaScript is running!';
            clientDiv.style.color = '#10b981';
            clientDiv.addEventListener('click', () => {
              clientDiv.textContent = 'Clicked at ' + new Date().toLocaleTimeString();
            });
          }
        });
      `;
      return new Response(clientJs, {
        headers: {
          'content-type': 'application/javascript',
        },
      });
    }
    
    // Serve HTML with both SSR and client content
    const html = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vite RSC Cloudflare POC</title>
        <style>
          body {
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
          }
          h1 { color: #3730a3; }
          .server { 
            background: #f3f4f6; 
            padding: 1rem; 
            border-radius: 0.5rem;
            margin: 1rem 0;
          }
          .client { 
            background: #fef3c7; 
            padding: 1rem; 
            border-radius: 0.5rem;
            margin: 1rem 0;
            cursor: pointer;
          }
        </style>
      </head>
      <body>
        <h1>Vite RSC + Cloudflare Workers</h1>
        
        <div class="server">
          <h2>Server-Side Rendered (SSR)</h2>
          <p>This content is rendered on Cloudflare Workers at ${new Date().toISOString()}</p>
        </div>
        
        <div class="client">
          <h2>Client-Side</h2>
          <p id="client-message">Loading client JavaScript...</p>
        </div>
        
        <script src="/client.js"></script>
      </body>
      </html>
    `;
    
    return new Response(html, {
      headers: {
        'content-type': 'text/html; charset=utf-8',
      },
    });
  },
}