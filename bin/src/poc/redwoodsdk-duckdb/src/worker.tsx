import { defineApp } from "rwsdk/worker";
import { route, render } from "rwsdk/router";
import { Document } from "@/app/Document";
import { Home } from "@/app/pages/Home";
import { setCommonHeaders } from "@/app/headers";
import { logInfo } from "@/utils/logger";

export type AppContext = {};

export default defineApp([
  setCommonHeaders(),
  async ({ request, env }) => {
    // Minimal logging for POC
    const url = new URL(request.url);
    logInfo(
      "server_request",
      `[POC] ${request.method} ${url.pathname}`,
      {
        method: request.method,
        path: url.pathname,
      }
    );
    
    // R2 WASM file serving endpoint
    if (url.pathname.startsWith('/r2/duckdb/')) {
      const filename = url.pathname.replace('/r2/duckdb/', '');
      const object = await env.R2_BUCKET?.get(`duckdb/${filename}`);
      
      if (object) {
        const headers = new Headers();
        headers.set('Content-Type', object.httpMetadata?.contentType || 'application/octet-stream');
        headers.set('Cache-Control', 'public, max-age=31536000, immutable');
        headers.set('Access-Control-Allow-Origin', '*');
        
        return new Response(object.body, { headers });
      }
      
      return new Response('Not Found', { status: 404 });
    }
  },
  render(Document, [
    route("/", [
      () => {
        logInfo(
          'home_route',
          'Serving DuckDB WASM POC'
        );
      },
      Home,
    ]),
  ]),
]);
