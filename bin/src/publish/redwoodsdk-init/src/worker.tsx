import { defineApp, ErrorResponse } from "rwsdk/worker";
import { route, render, prefix } from "rwsdk/router";
import { Document } from "@/app/Document";
import { Home } from "@/app/pages/Home";
import { TestForm } from "@/app/pages/TestForm";
import { setCommonHeaders } from "@/app/headers";
import { userRoutes } from "@/app/pages/user/routes";
import { sessions, setupSessionStore } from "./session/store";
import { Session } from "./session/durableObject";
import { type User, db, setupDb } from "@/db";
import { env } from "cloudflare:workers";
export { SessionDurableObject } from "./session/durableObject";

export type AppContext = {
  session: Session | null;
  user: User | null;
};

export default defineApp([
  setCommonHeaders(),
  async ({ ctx, request, headers }) => {
    // Production logging for wrangler tail
    const url = new URL(request.url);
    const timestamp = new Date().toISOString();
    console.log(JSON.stringify({
      timestamp,
      method: request.method,
      path: url.pathname,
      query: url.search,
      headers: {
        'user-agent': request.headers.get('user-agent'),
        'cf-ray': request.headers.get('cf-ray'),
        'x-forwarded-for': request.headers.get('x-forwarded-for'),
      },
      message: `[Server] ${request.method} ${url.pathname}`,
    }));
    
    await setupDb(env);
    setupSessionStore(env);

    try {
      ctx.session = await sessions.load(request);
      if (ctx.session) {
        console.log(JSON.stringify({
          timestamp: new Date().toISOString(),
          event: 'session_loaded',
          sessionId: ctx.session.id,
          userId: ctx.session.userId,
        }));
      }
    } catch (error) {
      console.error(JSON.stringify({
        timestamp: new Date().toISOString(),
        event: 'session_error',
        error: error instanceof Error ? error.message : String(error),
      }));
      
      if (error instanceof ErrorResponse && error.code === 401) {
        await sessions.remove(request, headers);
        headers.set("Location", "/user/login");

        return new Response(null, {
          status: 302,
          headers,
        });
      }

      throw error;
    }

    if (ctx.session?.userId) {
      ctx.user = await db.user.findUnique({
        where: {
          id: ctx.session.userId,
        },
      });
      if (ctx.user) {
        console.log(JSON.stringify({
          timestamp: new Date().toISOString(),
          event: 'user_loaded',
          userId: ctx.user.id,
          email: ctx.user.email,
        }));
      }
    }
  },
  render(Document, [
    route("/", () => {
      console.log(JSON.stringify({
        timestamp: new Date().toISOString(),
        event: 'home_route',
        message: 'Serving home page',
      }));
      return new Response("Hello, World!");
    }),
    route("/test-form", TestForm),
    route("/api/test-submit", async ({ request }) => {
      if (request.method !== "POST") {
        return new Response("Method not allowed", { status: 405 });
      }
      
      const formData = await request.formData();
      const data = {
        name: formData.get("name"),
        email: formData.get("email"),
        message: formData.get("message"),
      };
      
      // Structured logging for form submission
      console.log(JSON.stringify({
        timestamp: new Date().toISOString(),
        event: 'form_submission',
        type: 'test_form',
        method: request.method,
        data: data,
        headers: {
          'content-type': request.headers.get('content-type'),
          'origin': request.headers.get('origin'),
          'referer': request.headers.get('referer'),
        },
        metadata: {
          formFields: Object.keys(data),
          fieldCount: Object.keys(data).length,
        }
      }));
      
      return new Response(JSON.stringify({
        success: true,
        received: data,
        timestamp: new Date().toISOString(),
      }), {
        status: 200,
        headers: { 
          'Content-Type': 'application/json',
        },
      });
    }),
    route("/protected", [
      ({ ctx }) => {
        if (!ctx.user) {
          return new Response(null, {
            status: 302,
            headers: { Location: "/user/login" },
          });
        }
      },
      Home,
    ]),
    prefix("/user", userRoutes),
  ]),
]);
