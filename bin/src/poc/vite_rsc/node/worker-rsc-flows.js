// RSC Data Flow Implementation with Web Standard APIs only
// NO Node.js dependencies, NO external libraries

// Minimal RSC payload generator (simulating server component)
function generateRSCPayload(path) {
  return {
    type: 'fragment',
    key: null,
    props: {
      children: [
        {
          type: 'h1',
          props: { children: `RSC Flow: ${path}` }
        },
        {
          type: 'Counter',
          props: { initialCount: 0 },
          // This marks it as a client component reference
          $$typeof: 'react.element.client'
        }
      ]
    }
  };
}

// SSR function (minimal React-like rendering)
function renderToHTML(rscPayload) {
  function renderElement(element) {
    if (typeof element === 'string') return element;
    if (!element) return '';
    
    const { type, props } = element;
    
    // Handle client component placeholder
    if (element.$$typeof === 'react.element.client') {
      return `<div data-client-component="${type}" data-props='${JSON.stringify(props)}'>
        <h2>Counter: ${props.initialCount || 0}</h2>
        <button>-</button><button>+</button>
      </div>`;
    }
    
    // Handle regular elements
    if (typeof type === 'string') {
      const children = props?.children 
        ? (Array.isArray(props.children) 
            ? props.children.map(renderElement).join('') 
            : renderElement(props.children))
        : '';
      return `<${type}>${children}</${type}>`;
    }
    
    // Handle fragments
    if (type === 'fragment' && props?.children) {
      return Array.isArray(props.children) 
        ? props.children.map(renderElement).join('')
        : renderElement(props.children);
    }
    
    return '';
  }
  
  return renderElement(rscPayload);
}

// Client hydration script (inline for simplicity)
const hydrationScript = `
<script type="module">
// Find all client components and hydrate them
document.querySelectorAll('[data-client-component]').forEach(el => {
  const type = el.dataset.clientComponent;
  const props = JSON.parse(el.dataset.props || '{}');
  
  if (type === 'Counter') {
    let count = props.initialCount || 0;
    const updateCounter = () => {
      el.querySelector('h2').textContent = 'Counter: ' + count;
    };
    
    el.querySelectorAll('button').forEach((btn, i) => {
      btn.addEventListener('click', () => {
        count += (i === 0 ? -1 : 1);
        updateCounter();
      });
    });
  }
});
console.log('✅ Hydration complete');
</script>
`;

// CSR script that fetches and renders RSC payload
const csrScript = `
<script type="module">
async function fetchAndRenderRSC() {
  const response = await fetch(location.pathname, {
    headers: { 'Accept': 'application/rsc+json' }
  });
  const rscPayload = await response.json();
  
  // Simple client-side renderer
  function renderToDOM(element, container) {
    if (typeof element === 'string') {
      container.appendChild(document.createTextNode(element));
      return;
    }
    if (!element) return;
    
    const { type, props } = element;
    
    // Handle client components
    if (element.$$typeof === 'react.element.client' && type === 'Counter') {
      let count = props.initialCount || 0;
      const div = document.createElement('div');
      div.innerHTML = \`
        <h2>Counter: \${count}</h2>
        <button>-</button><button>+</button>
      \`;
      
      div.querySelectorAll('button').forEach((btn, i) => {
        btn.addEventListener('click', () => {
          count += (i === 0 ? -1 : 1);
          div.querySelector('h2').textContent = 'Counter: ' + count;
        });
      });
      
      container.appendChild(div);
      return;
    }
    
    // Handle regular elements
    if (typeof type === 'string') {
      const el = document.createElement(type);
      if (props?.children) {
        const children = Array.isArray(props.children) ? props.children : [props.children];
        children.forEach(child => renderToDOM(child, el));
      }
      container.appendChild(el);
      return;
    }
    
    // Handle fragments
    if (type === 'fragment' && props?.children) {
      const children = Array.isArray(props.children) ? props.children : [props.children];
      children.forEach(child => renderToDOM(child, container));
    }
  }
  
  const root = document.getElementById('root');
  root.innerHTML = '';
  renderToDOM(rscPayload, root);
  console.log('✅ CSR rendering complete');
}

fetchAndRenderRSC();
</script>
`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Serve assets
    if (url.pathname.startsWith('/assets/')) {
      return env.ASSETS.fetch(request);
    }
    
    // Route: RSC-SSR-CSR flow
    if (url.pathname === '/rsc-ssr-csr') {
      const rscPayload = generateRSCPayload('RSC-SSR-CSR');
      
      // Return RSC payload if requested
      if (request.headers.get('Accept')?.includes('application/rsc+json')) {
        return new Response(JSON.stringify(rscPayload), {
          headers: { 'content-type': 'application/rsc+json' }
        });
      }
      
      // SSR the RSC payload
      const ssrHTML = renderToHTML(rscPayload);
      
      return new Response(`<!DOCTYPE html>
<html>
<head>
  <title>RSC-SSR-CSR Flow</title>
  <style>
    body { font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 2rem; }
    button { padding: 0.5rem 1rem; margin: 0 0.5rem; font-size: 1.2rem; cursor: pointer; }
    h1 { color: #2563eb; }
    h2 { color: #059669; }
    .info { background: #f3f4f6; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
  </style>
</head>
<body>
  <div class="info">
    📋 Flow: RSC payload → SSR (server-rendered HTML) → CSR (hydration)
  </div>
  <div id="root">${ssrHTML}</div>
  ${hydrationScript}
</body>
</html>`, {
        headers: { 'content-type': 'text/html;charset=UTF-8' }
      });
    }
    
    // Route: RSC-CSR flow (no SSR)
    if (url.pathname === '/rsc-csr') {
      const rscPayload = generateRSCPayload('RSC-CSR');
      
      // Return RSC payload if requested
      if (request.headers.get('Accept')?.includes('application/rsc+json')) {
        return new Response(JSON.stringify(rscPayload), {
          headers: { 'content-type': 'application/rsc+json' }
        });
      }
      
      // Return minimal HTML that fetches RSC and renders on client
      return new Response(`<!DOCTYPE html>
<html>
<head>
  <title>RSC-CSR Flow</title>
  <style>
    body { font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 2rem; }
    button { padding: 0.5rem 1rem; margin: 0 0.5rem; font-size: 1.2rem; cursor: pointer; }
    h1 { color: #dc2626; }
    h2 { color: #059669; }
    .info { background: #fef3c7; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
  </style>
</head>
<body>
  <div class="info">
    📋 Flow: RSC payload → Direct CSR (no SSR, client fetches and renders)
  </div>
  <div id="root">Loading...</div>
  ${csrScript}
</body>
</html>`, {
        headers: { 'content-type': 'text/html;charset=UTF-8' }
      });
    }
    
    // Home page with links
    return new Response(`<!DOCTYPE html>
<html>
<head>
  <title>RSC Data Flows - Web Standard APIs</title>
  <style>
    body { font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 2rem; }
    h1 { color: #1e40af; }
    .flow-card {
      border: 2px solid #e5e7eb;
      padding: 1.5rem;
      margin: 1rem 0;
      border-radius: 0.5rem;
      transition: border-color 0.2s;
    }
    .flow-card:hover { border-color: #3b82f6; }
    .flow-card h2 { margin-top: 0; color: #059669; }
    .flow-card a {
      display: inline-block;
      padding: 0.5rem 1rem;
      background: #3b82f6;
      color: white;
      text-decoration: none;
      border-radius: 0.25rem;
      margin-top: 0.5rem;
    }
    .flow-card a:hover { background: #2563eb; }
    code { background: #f3f4f6; padding: 0.25rem; border-radius: 0.25rem; }
  </style>
</head>
<body>
  <h1>🚀 RSC Data Flow Demonstrations</h1>
  <p>Minimal implementations using <strong>Web Standard APIs only</strong> (no Node.js, no libraries)</p>
  
  <div class="flow-card">
    <h2>RSC → SSR → CSR</h2>
    <p>Full flow: Server components generate RSC payload, SSR renders HTML, client hydrates</p>
    <p>Path: <code>/rsc-ssr-csr</code></p>
    <a href="/rsc-ssr-csr">View Demo</a>
  </div>
  
  <div class="flow-card">
    <h2>RSC → CSR</h2>
    <p>Direct flow: Server components generate RSC payload, client fetches and renders directly</p>
    <p>Path: <code>/rsc-csr</code></p>
    <a href="/rsc-csr">View Demo</a>
  </div>
  
  <div class="flow-card" style="background: #f9fafb;">
    <h2>Implementation Details</h2>
    <ul>
      <li>✅ No Node.js dependencies</li>
      <li>✅ No external libraries (no React, no react-dom)</li>
      <li>✅ Web Standard APIs only</li>
      <li>✅ Works on Cloudflare Workers Edge</li>
      <li>✅ KISS + YAGNI principles</li>
    </ul>
  </div>
</body>
</html>`, {
      headers: { 'content-type': 'text/html;charset=UTF-8' }
    });
  }
};