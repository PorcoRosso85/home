// kuzu/terminal/serve.ts

import { start } from "./serve/start.ts";

// コマンドライン引数からポート番号を取得（デフォルトは8000）
const port = parseInt(Deno.args[0]) || 8000;

// サーバーを起動
await start(port);
console.log(`CLI Remote Server is running on http://localhost:${port}`);
