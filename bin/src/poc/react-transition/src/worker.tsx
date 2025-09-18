// Simple test component first - no React imports to isolate the issue
function App() {
  return `
    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
      <h1>🚀 React Transition Demo (Worker × SSR)</h1>
      <p style="color: #666; margin-bottom: 32px;">
        Interactive screen transition demonstration powered by Cloudflare Workers and Server-Side Rendering.
        This is a minimal test version to verify basic functionality.
      </p>
      
      <div style="padding: 16px; background: white; border-radius: 8px; margin-bottom: 24px; border: 1px solid #e0e0e0;">
        <h3 style="margin: 0 0 8px 0; color: #1976d2;">Status: Working</h3>
        <p style="margin: 0; color: #666;">Basic server-side rendering is functional.</p>
      </div>
      
      <div style="padding: 16px; background: #f8f9fa; border-radius: 8px; font-size: 14px; color: #666;">
        <strong>🏗️ Technical Implementation:</strong>
        <ul style="margin: 8px 0; padding-left: 20px;">
          <li><strong>Server-Side Rendering:</strong> Direct HTML string rendering</li>
          <li><strong>Edge Runtime:</strong> Cloudflare Workers deployment</li>
          <li><strong>Performance:</strong> Minimal bundle size</li>
        </ul>
      </div>
    </div>
  `;
}

export default {
  async fetch(request: Request, env: any): Promise<Response> {
    const url = new URL(request.url);
    
    // Handle asset requests
    if (url.pathname.startsWith('/assets/')) {
      const assetPath = url.pathname.slice('/assets/'.length);
      return env.ASSETS.fetch(new Request(`https://example.com/${assetPath}`, request));
    }
    
    // Get the simple HTML string
    const appHtml = App();
    
    // Return complete HTML with SSR content
    const html = `
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>React Transition Demo</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .navigation { display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
            .nav-item { 
              padding: 12px 18px; 
              background: #ffffff; 
              text-decoration: none; 
              color: #333; 
              border-radius: 8px; 
              box-shadow: 0 2px 4px rgba(0,0,0,0.1);
              border: 2px solid transparent;
              transition: all 0.2s ease;
            }
            .nav-item:hover { 
              background: #f8f9fa; 
              transform: translateY(-1px);
              box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .nav-item.active { 
              background: #007bff; 
              color: white; 
              border-color: #0056b3;
            }
            .breadcrumb { 
              margin-bottom: 25px; 
              color: #666; 
              font-size: 14px;
              background: white;
              padding: 10px 15px;
              border-radius: 6px;
              box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .page-content { 
              padding: 30px; 
              background: white; 
              border-radius: 12px; 
              box-shadow: 0 2px 8px rgba(0,0,0,0.1);
              line-height: 1.6;
            }
            .badge { 
              display: inline-block; 
              padding: 4px 8px; 
              margin-left: 8px; 
              font-size: 11px; 
              border-radius: 12px; 
              font-weight: 600;
              text-transform: uppercase;
              letter-spacing: 0.3px;
            }
            .auth-badge { background: #28a745; color: white; }
            .ssr-badge { background: #17a2b8; color: white; }
            .transition-button {
              transition: all 0.2s ease;
              font-family: inherit;
            }
            .transition-button:hover {
              transform: translateY(-1px);
              box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .interactive-demo {
              margin-top: 20px;
              padding: 20px;
              background: #f8f9fa;
              border-radius: 8px;
              border-left: 4px solid #007bff;
            }
          </style>
        </head>
        <body>
          <div id="root">${appHtml}</div>
          <script type="module" src="/assets/main.js"></script>
        </body>
      </html>
    `;
    
    return new Response(html, {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'public, max-age=300',
      },
    });
  },
};