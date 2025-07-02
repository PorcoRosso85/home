/**
 * 極限最適化サーバー - 1000クライアント挑戦
 */

import { createExtremeServer } from "./core.ts";
import type { ExtremeServerConfig } from "./types.ts";

// システム情報表示
console.log(`
🔥 EXTREME SERVER - 1000 CLIENT CHALLENGE 🔥
==========================================
CPU Cores: ${navigator.hardwareConcurrency || "unknown"}
Platform: ${Deno.build.os}
Deno Version: ${Deno.version.deno}
V8 Version: ${Deno.version.v8}
==========================================
`);

// 極限設定
const config: ExtremeServerConfig = {
  port: parseInt(Deno.env.get("PORT") || "3000"),
  maxMetricsSize: 50000, // 大量のメトリクス
  maxConcurrentRequests: 200, // 同時処理数
  cacheSize: 2000, // 大きなキャッシュ
  cacheTTL: 120000, // 2分
  
  // TCP最適化
  tcpNoDelay: true,
  tcpKeepAlive: true,
  tcpKeepAliveInitialDelay: 10000, // 10秒
  
  // 接続制限
  maxConnectionsPerIP: 50,
  connectionTimeout: 30000, // 30秒
  
  // キューサイズ
  requestQueueSize: 1000,
  
  // バッファプール
  preallocateBuffers: 1500, // 1500個のバッファを事前確保
  
  // ゼロコピー（将来の拡張用）
  enableZeroCopy: true,
};

// 警告表示
console.warn(`
⚠️  WARNING: This server attempts to handle 1000 concurrent connections!
⚠️  System limits may be reached. Monitor resource usage carefully.
⚠️  Recommended system tuning:
    - ulimit -n 65536
    - sysctl -w net.core.somaxconn=4096
    - sysctl -w net.ipv4.tcp_max_syn_backlog=4096
`);

// サーバー作成
const server = createExtremeServer(config);

// グレースフルシャットダウン
let shuttingDown = false;

Deno.addSignalListener("SIGTERM", () => {
  if (shuttingDown) return;
  shuttingDown = true;
  
  console.log("\n🛑 Graceful shutdown initiated...");
  server.stop();
  
  // 接続のドレイン待機
  setTimeout(() => {
    console.log("👋 Goodbye!");
    Deno.exit(0);
  }, 5000);
});

Deno.addSignalListener("SIGINT", () => {
  if (shuttingDown) return;
  shuttingDown = true;
  
  console.log("\n🛑 Shutdown requested...");
  server.stop();
  Deno.exit(0);
});

// メモリ使用量の定期レポート
setInterval(() => {
  const memory = Deno.memoryUsage();
  console.log(`
📊 Memory Report:
  RSS: ${(memory.rss / 1024 / 1024).toFixed(2)}MB
  Heap Used: ${(memory.heapUsed / 1024 / 1024).toFixed(2)}MB
  Heap Total: ${(memory.heapTotal / 1024 / 1024).toFixed(2)}MB
  External: ${(memory.external / 1024 / 1024).toFixed(2)}MB
  `);
}, 30000); // 30秒ごと

// サーバー起動
try {
  await server.start();
} catch (error) {
  console.error("❌ Failed to start server:", error);
  Deno.exit(1);
}