import { renderToReadableStream } from '@vitejs/plugin-rsc/rsc'
import App from '../app/App'

// HTML wrapper component for server rendering
function AppWrapper() {
  return (
    <html>
      <head>
        <title>Vite RSC POC</title>
      </head>
      <body>
        <div id="root">
          <App />
        </div>
      </body>
    </html>
  );
}

// RSC request handler following @vitejs/plugin-rsc pattern
async function handler(request: Request): Promise<Response> {
  // Serialize React VDOM to RSC stream
  const root = <AppWrapper />
  const rscStream = renderToReadableStream(root)

  // Handle direct RSC stream requests (ending with .rsc)
  if (request.url.endsWith('.rsc')) {
    return new Response(rscStream, {
      headers: {
        'Content-Type': 'text/x-component;charset=utf-8',
      },
    })
  }

  // Delegate to SSR environment for HTML rendering
  // loadModule is a helper API provided by the plugin for multi-environment interaction
  const ssrEntry = await import.meta.viteRsc.loadModule<
    typeof import('./entry.ssr.tsx')
  >('ssr', 'index')
  
  // Load bootstrap script for client hydration
  const bootstrapScriptContent = await import.meta.viteRsc.loadBootstrapScriptContent('index')
  
  const htmlStream = await ssrEntry.handleSsr(rscStream, bootstrapScriptContent)

  // Return HTML response
  return new Response(htmlStream, {
    headers: {
      'Content-Type': 'text/html',
    },
  })
}

// Cloudflare Workers entry point
export default {
  fetch(request: Request) {
    return handler(request)
  },
}