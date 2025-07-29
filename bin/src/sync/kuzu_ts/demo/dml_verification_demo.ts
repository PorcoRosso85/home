/**
 * DML Verification Demo
 * DML実行を可視化する同期デモ
 */

import { SyncKuzuClient } from "../mod.ts";
import * as telemetry from "../telemetry_log.ts";

const clientId = Deno.args[0] || "dml-demo-client-1";
const clientName = Deno.args[1] || "DML Demo Client 1";

telemetry.info("=== DML Verification Demo Starting ===", {
  clientId,
  clientName,
  timestamp: new Date().toISOString()
});

const client = new SyncKuzuClient({ clientId });

try {
  // 初期化
  await client.initialize();
  telemetry.info("SyncKuzuClient initialized", { clientId });
  
  // サーバー接続
  await client.connect("ws://localhost:8080");
  telemetry.info("Connected to sync server", { clientId });
  
  // 統計レポーター開始
  client.startStatsReporter();
  
  // テンプレート定義
  const templates = [
    {
      name: "CREATE_USER",
      params: () => ({
        userId: `user-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        name: `${clientName} User ${Math.floor(Math.random() * 100)}`,
        email: `user${Date.now()}@example.com`
      })
    },
    {
      name: "CREATE_POST", 
      params: () => ({
        postId: `post-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        content: `Message from ${clientName} at ${new Date().toLocaleTimeString()}`,
        authorId: "user-demo"
      })
    },
    {
      name: "CREATE_FOLLOW",
      params: () => ({
        followerId: `user-${Math.floor(Math.random() * 10)}`,
        followeeId: `user-${Math.floor(Math.random() * 10)}`
      })
    }
  ];
  
  // 定期的にイベント送信
  let counter = 0;
  const interval = setInterval(async () => {
    const template = templates[counter % templates.length];
    
    try {
      telemetry.info(`\n=== Executing template: ${template.name} ===`, { clientId });
      const event = await client.executeTemplate(template.name, template.params());
      
      telemetry.info("✅ Template executed successfully", {
        clientId,
        eventId: event.id,
        template: template.name,
        counter: counter++
      });
    } catch (error) {
      telemetry.error("❌ Template execution failed", {
        clientId,
        template: template.name,
        error: error.message
      });
    }
  }, 2000); // 2秒ごと
  
  // 終了処理
  process.on("SIGINT", async () => {
    telemetry.info("\n=== Shutting down ===", { clientId });
    
    clearInterval(interval);
    client.stopStatsReporter();
    
    // 最終統計を表示
    const stats = client.getDMLStats();
    const detailedStats = client.getDetailedStatsByTemplate();
    
    telemetry.info("Final DML Statistics", {
      clientId,
      overall: stats,
      byTemplate: detailedStats
    });
    
    await client.close();
    Deno.exit(0);
  });
  
} catch (error) {
  telemetry.error("Demo initialization failed", {
    clientId,
    error: error.message
  });
  Deno.exit(1);
}