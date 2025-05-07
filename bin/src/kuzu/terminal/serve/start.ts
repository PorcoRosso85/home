// kuzu/terminal/serve/start.ts

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { handleRequest } from "./handler.ts";

/**
 * 指定されたポートでサーバーを起動する
 * @param port サーバーが待ち受けるポート番号
 */
export async function start(port: number): Promise<void> {
  await serve(handleRequest, { port });
}
