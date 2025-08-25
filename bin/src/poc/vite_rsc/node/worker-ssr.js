// Edge-compatible SSR implementation
import React from 'react';
import { renderToReadableStream } from 'react-dom/server.edge';

// Simple Counter component (inline for Edge compatibility)
function Counter() {
  // Note: This is SSR, so no interactivity yet
  return React.createElement('div', { className: 'counter' },
    React.createElement('h2', null, 'Counter: 0'),
    React.createElement('div', { className: 'buttons' },
      React.createElement('button', null, '-'),
      React.createElement('button', null, '+')
    )
  );
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Serve assets
    if (url.pathname.startsWith('/assets/')) {
      return env.ASSETS.fetch(request);
    }
    
    // SSR the Counter component
    const stream = await renderToReadableStream(
      React.createElement(Counter)
    );
    
    const html = `<!DOCTYPE html>
<html>
<head>
  <title>Edge SSR Counter</title>
  <style>
    body { font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 2rem; }
    .counter { text-align: center; padding: 2rem; border: 2px solid #e2e8f0; border-radius: 8px; }
    .buttons { margin-top: 1rem; }
    button { padding: 0.5rem 1rem; margin: 0 0.5rem; font-size: 1.2rem; cursor: pointer; }
  </style>
</head>
<body>
  <h1>Edge SSR Demo</h1>
  <div id="root">${await streamToString(stream)}</div>
  <script type="module">
    // Hydration code would go here
    console.log('SSR rendered, ready for hydration');
  </script>
</body>
</html>`;
    
    return new Response(html, {
      headers: { 'content-type': 'text/html;charset=UTF-8' }
    });
  }
};

async function streamToString(stream) {
  const reader = stream.getReader();
  let result = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    result += new TextDecoder().decode(value);
  }
  return result;
}