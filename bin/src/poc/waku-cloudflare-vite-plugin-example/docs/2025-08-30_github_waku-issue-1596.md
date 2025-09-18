---
url: https://github.com/wakujs/waku/issues/1596
saved_at: 2025-08-30T00:00:00Z
title: It should be possible to use @cloudflare/vite-plugin #1596
domain: github.com
---

# It should be possible to use @cloudflare/vite-plugin #1596

[@rmarscher](https://github.com/rmarscher) opened on Aug 5, 2025

## Description

Waku has migrated to use @vitejs/plugin-rsc and Vite's Environment API which paves the way for integrating @cloudflare/vite-plugin - as mentioned in the blog post [https://waku.gg/blog/migration-to-vite-plugin-rsc](https://waku.gg/blog/migration-to-vite-plugin-rsc).

Waku now uses three Vite environments. One for `client`, another for `ssr` (which is optional), and one for `rsc`. The rsc environment invokes functions to render html that run in the ssr environment - using this code: [https://github.com/wakujs/waku/blob/v0.24.0/packages/waku/src/vite-rsc/lib/render.ts#L66-L73](https://github.com/wakujs/waku/blob/v0.24.0/packages/waku/src/vite-rsc/lib/render.ts#L66-L73)

The Cloudflare Vite plugin requires pointing to an entry file in the `main` property of the wrangler.jsonc.

Maybe we can move [createApp](https://github.com/wakujs/waku/blob/v0.24.0/packages/waku/src/vite-rsc/entry.server.tsx#L12) to [src/vite-rsc/lib/engine.ts](https://github.com/wakujs/waku/blob/v0.24.0/packages/waku/src/vite-rsc/lib/engine.ts) and export it from `waku`.

That would give a lot of flexibility for devs to create their own entry for their app and point to it in wrangler.jsonc - and we can supply a default in the 07_cloudflare template.

Cloudflare's Vite plugin only allows specifying one environment in its config. I think we only need it for the rsc environment since that calls the ssr environment... but I'm not really sure yet if the ssr environment would then run in nodejs, but that's probably not a really big deal as long as the bindings and execution context are available.

To reproduce, create a waku project with the 07_cloudflare template ( `npm create waku@latest --template 07_cloudflare`), add `@cloudflare/vite-plugin` to your project from npm and then add the cloudflare plugin. You'll get an error about the entry point - "The provided Wrangler config main field (.../dist/worker/serve-cloudflare.js) doesn't point to an existing file."

```javascript
import { defineConfig } from 'waku/config';
import { cloudflare } from "@cloudflare/vite-plugin";

export default defineConfig({
  // we may be able replace the hono enhancer with a new context plugin
  unstable_honoEnhancer: './waku.hono-enhancer',
  middleware: [
    'waku/middleware/context',
    'waku/middleware/dev-server',
    './waku.cloudflare-middleware',
    'waku/middleware/handler',
  ],
  vite: {
    plugins: [
      cloudflare({
        viteEnvironment: { name: "rsc" }
      }),
    ],
  }
});
```

Once we figure out the entry point, there might be some things to adjust with the hono enhancer and middleware plugin.

Fixing this should fix a few other open issues about Waku and Cloudflare like [#1245](https://github.com/wakujs/waku/issues/1245).