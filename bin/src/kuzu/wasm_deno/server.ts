#!/usr/bin/env -S nix run nixpkgs#deno -- run --allow-net --allow-read

import { serve } from "https://deno.land/std@0.204.0/http/server.ts";

// 静的ファイルを提供する関数
async function serveFile(path: string, contentType: string): Promise<Response> {
  try {
    const file = await Deno.readFile(path);
    return new Response(file, {
      headers: {
        "content-type": contentType,
        "Cross-Origin-Embedder-Policy": "require-corp",
        "Cross-Origin-Opener-Policy": "same-origin"
      }
    });
  } catch (error) {
    console.error(`Error serving file ${path}:`, error);
    return new Response(`Error: ${error.message}`, { status: 500 });
  }
}

// HTTPサーバーを起動
serve(async (req: Request) => {
  const url = new URL(req.url);
  const path = url.pathname;
  
  console.log(`Request: ${path}`);

  if (path === "/" || path === "/index.html") {
    return await serveFile("./public/index.html", "text/html; charset=utf-8");
  } else if (path === "/browser.ts") {
    return await serveFile("./public/browser.ts", "application/typescript; charset=utf-8");
  } else {
    return new Response("Not Found", { status: 404 });
  }
}, { port: 8000 });

console.log("Server running at http://localhost:8000/");
