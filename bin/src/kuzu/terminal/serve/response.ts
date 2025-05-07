// kuzu/terminal/serve/response.ts

import { RPCResponse } from "./types.ts";

/**
 * 成功レスポンスを生成する
 * @param id リクエストID
 * @param result 結果オブジェクト
 * @returns JSON-RPC 2.0レスポンスオブジェクト
 */
export function createSuccessResponse(id: string | number | null, result: any): RPCResponse {
  return {
    jsonrpc: "2.0",
    id,
    result,
  };
}

/**
 * エラーレスポンスを生成する
 * @param id リクエストID
 * @param code エラーコード
 * @param message エラーメッセージ
 * @param data 追加のエラーデータ（オプション）
 * @returns JSON-RPC 2.0エラーレスポンスオブジェクト
 */
export function createErrorResponse(
  id: string | number | null, 
  code: number, 
  message: string, 
  data?: any
): RPCResponse {
  return {
    jsonrpc: "2.0",
    id,
    error: {
      code,
      message,
      ...(data ? { data } : {}),
    },
  };
}

/**
 * ストリームイベントを生成する
 * @param id リクエストID
 * @param method イベントメソッド名（"stdout" or "stderr"）
 * @param data イベントデータ
 * @returns ストリームイベントオブジェクト
 */
export function createStreamEvent(
  id: string | number, 
  method: string, 
  data: string
): string {
  return `data: ${JSON.stringify({
    jsonrpc: "2.0",
    method,
    params: {
      id,
      data,
    },
  })}\n\n`;
}
