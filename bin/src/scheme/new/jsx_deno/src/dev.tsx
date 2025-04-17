import React from "react";
import { renderToString } from "react-dom/server";

// Import page components
import { HomePage } from "./pages/index.tsx";
import { AboutPage } from "./pages/about.tsx";

// Routes configuration
const ROUTES = [
  { component: HomePage, path: "/" },
  { component: AboutPage, path: "/about" },
];

// Simple development server
const server = Deno.listen({ port: 3000 });
console.log("Dev server running at http://localhost:3000/");

for await (const conn of server) {
  serveHttp(conn).catch(console.error);
}

async function serveHttp(conn: Deno.Conn) {
  const httpConn = Deno.serveHttp(conn);
  
  for await (const requestEvent of httpConn) {
    try {
      const url = new URL(requestEvent.request.url);
      const path = url.pathname;
      
      // Serve static files from public directory
      if (path.startsWith("/styles.css")) {
        const file = await Deno.readFile("./public/styles.css");
        await requestEvent.respondWith(
          new Response(file, {
            status: 200,
            headers: {
              "content-type": "text/css",
            },
          })
        );
        continue;
      }
      
      // Find matching route
      const route = ROUTES.find((r) => r.path === path || r.path === path + "/");
      
      if (route) {
        // Render the React component to HTML
        const html = "<!DOCTYPE html>\n" + renderToString(React.createElement(route.component));
        
        await requestEvent.respondWith(
          new Response(html, {
            status: 200,
            headers: {
              "content-type": "text/html; charset=utf-8",
            },
          })
        );
      } else {
        // 404 Not Found
        await requestEvent.respondWith(
          new Response("404 Not Found", { status: 404 })
        );
      }
    } catch (error) {
      console.error(error);
      await requestEvent.respondWith(
        new Response("500 Internal Server Error", { status: 500 })
      );
    }
  }
}
