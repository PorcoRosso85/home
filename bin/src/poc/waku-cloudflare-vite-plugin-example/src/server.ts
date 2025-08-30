import { createHonoHandler, importHono } from 'waku/unstable_hono';

// Reimplement rather than use the `'waku/server'` export
// since that causes node:fs to be imported
export function INTERNAL_setAllEnv(newEnv: Readonly<Record<string, string>>) {
  (globalThis as any).__WAKU_SERVER_ENV__ = newEnv;
}

const { Hono } = await importHono();
const app = new Hono<{ Bindings: Env }>();
app.use(createHonoHandler());
app.notFound(async (c) => {
  const assetsFetcher = c.env.ASSETS;
  const url = new URL(c.req.raw.url);
  const errorHtmlUrl = url.origin + '/404.html';
  const notFoundStaticAssetResponse = await assetsFetcher.fetch(
    new URL(errorHtmlUrl),
  );
  if (
    notFoundStaticAssetResponse &&
    notFoundStaticAssetResponse.status < 400
  ) {
    return c.body(notFoundStaticAssetResponse.body, 404);
  }
  return c.text('404 Not Found', 404);
});

function bindingsToWakuEnv(env: Env | Record<string, unknown>): Record<string, string> {
  const wakuEnv: Record<string, string> = {};
  for (const [key, value] of Object.entries(env)) {
    if (value === null || value === undefined || typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      wakuEnv[key] = `${value}`;
    }
  }
  return wakuEnv;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    INTERNAL_setAllEnv(bindingsToWakuEnv(env));
    return app.fetch(request, env, ctx);
  },
};
