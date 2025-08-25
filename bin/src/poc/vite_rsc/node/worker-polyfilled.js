// Improved Cloudflare Worker entry point with proper polyfills and module bundling
// This implementation addresses AsyncLocalStorage polyfill, module resolution, and error handling

// 1. Import AsyncLocalStorage polyfill FIRST (critical for RSC context)
import './polyfill-async-local-storage.js';

// 2. Import bundled RSC and SSR modules to handle resolution issues
import { renderToReadableStream as renderRSC } from '@vitejs/plugin-rsc/rsc';
import { createFromReadableStream, renderToReadableStream as renderSSR } from '@vitejs/plugin-rsc/ssr';
import React from 'react';

// 3. Inline the app components to avoid module resolution issues
const Counter = () => {
  const [count, setCount] = React.useState(0);
  return React.createElement('div', null, 
    React.createElement('p', null, `Count: ${count}`),
    React.createElement('button', { onClick: () => setCount(c => c + 1) }, 'Increment')
  );
};

const App = () => {
  return React.createElement('div', null,
    React.createElement('h1', null, 'Vite RSC on Cloudflare Workers'),
    React.createElement('p', null, 'React Server Components working with polyfilled AsyncLocalStorage'),
    React.createElement(Counter)
  );
};

const AppWrapper = () => {
  return React.createElement('html', null,
    React.createElement('head', null,
      React.createElement('title', null, 'Vite RSC POC - Polyfilled'),
      React.createElement('style', null, `
        body { font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 2rem; }
        button { padding: 0.5rem 1rem; margin: 0.5rem; cursor: pointer; }
        .error { background: #fee; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
      `)
    ),
    React.createElement('body', null,
      React.createElement('div', { id: 'root' }, React.createElement(App))
    )
  );
};

// 4. RSC request handler with proper error boundaries
async function handleRSCRequest(request) {
  try {
    const root = React.createElement(AppWrapper);
    const rscStream = renderRSC(root);

    // Direct RSC stream for .rsc requests
    if (request.url.endsWith('.rsc')) {
      return new Response(rscStream, {
        headers: {
          'Content-Type': 'text/x-component;charset=utf-8',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
      });
    }

    // Convert RSC to HTML via SSR
    const Component = await createFromReadableStream(rscStream);
    const htmlStream = await renderSSR(Component, {
      bootstrapScriptContent: `
        console.log('Vite RSC hydrated with polyfilled environment');
        // Initialize client-side interactivity if needed
      `
    });

    return new Response(htmlStream, {
      headers: {
        'Content-Type': 'text/html;charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
    });

  } catch (error) {
    console.error('RSC/SSR processing error:', error);
    throw error; // Re-throw to trigger fallback
  }
}

// 5. Fallback CSR implementation
function createCSRFallback(error) {
  return new Response(`<!DOCTYPE html>
<html>
<head>
  <title>Vite RSC - Fallback Mode</title>
  <style>
    body { font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 2rem; }
    .error { background: #fee; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
    .fallback { background: #ffe; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
  </style>
</head>
<body>
  <div class="fallback">
    <h2>Client-Side Rendering Mode</h2>
    <p>RSC processing failed, using client-side fallback.</p>
  </div>
  <div class="error">
    <details>
      <summary>Error Details</summary>
      <pre>${error.message}\n${error.stack}</pre>
    </details>
  </div>
  <div id="root">
    <h1>Vite RSC POC - CSR Fallback</h1>
    <p>This content is rendered client-side due to server processing error.</p>
  </div>
  <script type="module">
    // Basic client-side app as fallback
    const root = document.getElementById('root');
    root.innerHTML = \`
      <h1>Vite RSC POC - CSR Fallback</h1>
      <p>AsyncLocalStorage polyfill loaded: \${typeof globalThis.AsyncLocalStorage !== 'undefined'}</p>
      <p>Client-side rendering active due to server error.</p>
    \`;
  </script>
</body>
</html>`, {
    headers: { 
      'content-type': 'text/html;charset=UTF-8',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
    },
  });
}

// Main Worker export
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Serve static assets through Workers Assets
    if (url.pathname.startsWith('/assets/')) {
      return env.ASSETS?.fetch(request) || new Response('Asset not found', { status: 404 });
    }
    
    // Health check endpoint
    if (url.pathname === '/health') {
      return Response.json({
        status: 'ok',
        polyfills: {
          AsyncLocalStorage: typeof globalThis.AsyncLocalStorage !== 'undefined'
        },
        timestamp: new Date().toISOString()
      });
    }

    // Handle RSC/SSR requests with comprehensive error handling
    try {
      return await handleRSCRequest(request);
    } catch (error) {
      console.error('Worker request error:', error);
      return createCSRFallback(error);
    }
  },
};