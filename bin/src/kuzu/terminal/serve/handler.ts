// kuzu/terminal/serve/handler.ts

import { executeRpc } from "./rpc.ts";
import { createErrorResponse } from "./response.ts";
import { RPC_ERRORS } from "./constants.ts";

/**
 * HTTPリクエストを処理する
 * @param request HTTPリクエストオブジェクト
 * @returns HTTPレスポンスオブジェクト
 */
export async function handleRequest(request: Request): Promise<Response> {
  // リクエストの基本情報をログ出力
  const url = new URL(request.url);
  console.log(`[${new Date().toISOString()}] ${request.method} ${url.pathname}`);
  
  // POSTリクエストのみを受け付ける
  if (request.method !== "POST") {
    console.log(`Method not allowed: ${request.method}`);
    
    // OPTIONS (プリフライトリクエスト) の場合はCORSヘッダーを返す
    if (request.method === "OPTIONS") {
      return new Response(null, { 
        status: 204, 
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
          "Access-Control-Max-Age": "86400",
        }
      });
    }
    
    return new Response("Method Not Allowed", { 
      status: 405,
      headers: {
        "Access-Control-Allow-Origin": "*"
      }
    });
  }

  // URLパスに基づいて処理を分岐
  if (url.pathname === "/rpc") {
    try {
      // リクエストボディをJSONとしてパース
      let body;
      try {
        body = await request.json();
        console.log("Request body:", JSON.stringify(body, null, 2));
      } catch (error) {
        console.log("JSON parse error:", error.message);
        return new Response(
          JSON.stringify(createErrorResponse(null, RPC_ERRORS.PARSE_ERROR, "Invalid JSON")),
          { 
            headers: { 
              "content-type": "application/json",
              "Access-Control-Allow-Origin": "*"
            }, 
            status: 400 
          }
        );
      }
      
      // ダミーレスポンスは削除（実際のコマンド実行のみを使用）
      
      // JSON-RPC 2.0リクエストを処理
      try {
        const response = await executeRpc(body);
        
        // CORSヘッダーを追加
        const responseHeaders = new Headers(response.headers);
        responseHeaders.set("Access-Control-Allow-Origin", "*");
        
        return new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders
        });
      } catch (error) {
        console.error("RPC実行エラー:", error);
        return new Response(
          JSON.stringify(createErrorResponse(body.id, RPC_ERRORS.INTERNAL_ERROR, `Internal server error: ${error.message}`)),
          { 
            headers: { 
              "content-type": "application/json",
              "Access-Control-Allow-Origin": "*"
            }, 
            status: 500 
          }
        );
      }
    } catch (error) {
      console.error("Unexpected error:", error.message);
      // JSONパースエラーなどの例外を処理
      return new Response(
        JSON.stringify(createErrorResponse(null, RPC_ERRORS.INTERNAL_ERROR, `Unexpected error: ${error.message}`)),
        { 
          headers: { 
            "content-type": "application/json",
            "Access-Control-Allow-Origin": "*"
          }, 
          status: 500 
        }
      );
    }
  }
  
  // 不明なパスに対しては404を返す
  console.log(`Not found: ${url.pathname}`);
  return new Response("Not Found", { 
    status: 404,
    headers: {
      "Access-Control-Allow-Origin": "*"
    }
  });
}
