/**
 * Local HTTP Server for Playwright tests
 * KuzuDB WASMファイルを適切なヘッダーで配信
 */

const PORT = 3000;

console.log(`HTTP server starting on http://localhost:${PORT}`);

Deno.serve({ port: PORT }, async (req) => {
  const url = new URL(req.url);
  
  // Cross-Origin Isolation headers (KuzuDB multithreaded用)
  const headers = new Headers({
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Content-Type": "text/html; charset=utf-8"
  });
  
  if (url.pathname === "/") {
    return new Response(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>KuzuDB WASM Test Server</title>
      </head>
      <body>
        <h1>KuzuDB WASM Test Server</h1>
        <p>Ready for Playwright tests</p>
      </body>
      </html>
    `, { headers });
  }
  
  // node_modules内のファイルを配信
  if (url.pathname.startsWith("/node_modules/")) {
    try {
      const filePath = `.${url.pathname}`;
      const file = await Deno.readFile(filePath);
      
      const contentType = url.pathname.endsWith('.js') ? 'application/javascript' :
                         url.pathname.endsWith('.wasm') ? 'application/wasm' :
                         'application/octet-stream';
      
      return new Response(file, {
        headers: {
          "Content-Type": contentType,
          "Cross-Origin-Embedder-Policy": "require-corp",
          "Cross-Origin-Opener-Policy": "same-origin"
        }
      });
    } catch {
      return new Response("Not found", { status: 404 });
    }
  }
  
  return new Response("Not found", { status: 404 });
});