// メインエントリーポイント
// bin/docs規約準拠

import { DualServerApplication } from "./src/mod.ts";
import type { ServerConfig } from "./src/mod.ts";

// 起動スクリプト
if (import.meta.main) {
  const config: ServerConfig = {
    name: Deno.env.get('SERVER_NAME') || 'server-1',
    port: parseInt(Deno.env.get('PORT') || '3001'),
    partitionKey: Deno.env.get('PARTITION_KEY') || 'A-M',
    peerServer: Deno.env.get('PEER_SERVER') || 'http://localhost:3002',
    database: {
      hostname: Deno.env.get('DB_HOST') || 'localhost',
      port: parseInt(Deno.env.get('DB_PORT') || '5432'),
      database: Deno.env.get('DB_NAME') || 'server1_db',
      user: Deno.env.get('DB_USER') || 'dbuser',
      password: Deno.env.get('DB_PASSWORD') || 'dbpass'
    }
  };
  
  const server = new DualServerApplication(config);
  await server.start();
}