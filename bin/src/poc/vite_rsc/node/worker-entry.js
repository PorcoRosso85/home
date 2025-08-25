export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname.startsWith('/assets/')) {
      return env.ASSETS.fetch(request);
    }
    return new Response(`<!DOCTYPE html>
<html>
<head>
  <title>Counter CSR</title>
  <style>
    body { font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 2rem; }
    .counter { text-align: center; padding: 2rem; }
    .buttons { margin-top: 1rem; }
    button { padding: 0.5rem 1rem; margin: 0 0.5rem; font-size: 1.2rem; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/assets/index-BIf5sdHw.js"></script>
  <script type="module" src="/assets/Counter-BPR1mKj2.js"></script>
</body>
</html>`, {
      headers: { 'content-type': 'text/html;charset=UTF-8' },
    });
  },
};