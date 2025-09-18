export interface Env {
  CACHE: KVNamespace;
  FILES_BUCKET: R2Bucket;
}

async function handleKv(env: Env, req: Request, url: URL) {
  const key = url.pathname.replace(/^\/kv\//, "");
  if (!key) return new Response("KV key required", { status: 400 });

  if (req.method === "GET") {
    const value = await env.CACHE.get(key);
    if (value == null) return new Response("Not found", { status: 404 });
    return new Response(value, { status: 200, headers: { "Content-Type": "text/plain" } });
  }

  if (req.method === "PUT" || req.method === "POST") {
    const body = await req.text();
    await env.CACHE.put(key, body);
    return new Response("OK", { status: 201 });
  }

  if (req.method === "DELETE") {
    await env.CACHE.delete(key);
    return new Response(null, { status: 204 });
  }

  return new Response("Method not allowed", { status: 405 });
}

async function handleR2(env: Env, req: Request, url: URL) {
  const key = url.pathname.replace(/^\/r2\//, "");
  if (!key) return new Response("R2 key required", { status: 400 });

  if (req.method === "GET") {
    const obj = await env.FILES_BUCKET.get(key);
    if (!obj) return new Response("Not found", { status: 404 });
    return new Response(obj.body, {
      status: 200,
      headers: { "Content-Type": obj.httpMetadata?.contentType ?? "application/octet-stream" },
    });
  }

  if (req.method === "PUT" || req.method === "POST") {
    const contentType = req.headers.get("content-type") ?? "application/octet-stream";
    await env.FILES_BUCKET.put(key, req.body, { httpMetadata: { contentType } });
    return new Response("OK", { status: 201 });
  }

  if (req.method === "DELETE") {
    await env.FILES_BUCKET.delete(key);
    return new Response(null, { status: 204 });
  }

  return new Response("Method not allowed", { status: 405 });
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === "/") {
      return new Response(
        JSON.stringify({ ok: true, name: "shiorin-diary", env: "staging" }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    if (url.pathname.startsWith("/kv/")) {
      return handleKv(env, req, url);
    }

    if (url.pathname.startsWith("/r2/")) {
      return handleR2(env, req, url);
    }

    return new Response("Not found", { status: 404 });
  },
} satisfies ExportedHandler<Env>;

