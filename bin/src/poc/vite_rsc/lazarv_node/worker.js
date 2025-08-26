// Cloudflare Worker entry point
// This wraps the @lazarv/react-server build output for Cloudflare Workers

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Simple response for now since adapter is not available
    return new Response(`
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>React Server Components on Cloudflare</title>
      </head>
      <body>
        <h1>@lazarv/react-server on Cloudflare Workers</h1>
        <p>This is a proof of concept deployment.</p>
        <p>The official Cloudflare adapter is still in development.</p>
        <p>Path: ${url.pathname}</p>
      </body>
      </html>
    `, {
      headers: {
        'Content-Type': 'text/html;charset=UTF-8',
      }
    });
  }
};