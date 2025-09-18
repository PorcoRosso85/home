#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-net --allow-read --check

/**
 * 関数型スキーマ可視化のためのサーバーエントリポイント
 * 
 * 静的ファイルを提供し、APIエンドポイントも提供します。
 */

import { serve } from "https://deno.land/std/http/server.ts";
import { handler } from "./server/handler.ts";

// 設定
const PORT = 8080;

// サーバーの起動
console.log(`関数型スキーマ可視化サーバーをポート ${PORT} で起動しています...`);
await serve(handler, { port: PORT });
