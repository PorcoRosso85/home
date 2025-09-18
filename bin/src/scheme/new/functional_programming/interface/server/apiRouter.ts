/**
 * APIルーター
 * 
 * APIリクエストを適切なハンドラーに振り分けます。
 */

import { handleApiRequest as handleIntegratedApi } from './handler_api.ts';

/**
 * APIリクエストを処理
 * @param path リクエストパス
 * @param req HTTPリクエスト
 * @returns HTTPレスポンス
 */
export async function handleApiRequest(path: string, req: Request): Promise<Response> {
  // 統合APIエンドポイント
  // "/api"だけでなく"/api/xxx"のようなパスも受け付ける
  if (path.startsWith("/api")) {
    return handleIntegratedApi(req);
  }
  
  return new Response("不明なAPIエンドポイント", { status: 404 });
}
