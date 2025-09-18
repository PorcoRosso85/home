#!/usr/bin/env -S deno run -A
/**
 * E2Eテスト実行スクリプト
 * 前提条件の確認を含む
 */

async function checkViteServer(): Promise<boolean> {
  try {
    const response = await fetch("http://localhost:5173");
    return response.ok;
  } catch {
    return false;
  }
}

async function checkRPCServer(): Promise<boolean> {
  try {
    const ws = new WebSocket("ws://localhost:8080");
    return await new Promise<boolean>((resolve) => {
      const timeout = setTimeout(() => {
        ws.close();
        resolve(false);
      }, 1000);
      
      ws.onopen = () => {
        clearTimeout(timeout);
        ws.close();
        resolve(true);
      };
      
      ws.onerror = () => {
        clearTimeout(timeout);
        resolve(false);
      };
    });
  } catch {
    return false;
  }
}

async function main() {
  console.log("🔍 E2Eテスト前提条件確認中...\n");
  
  // Viteサーバー確認
  const viteOk = await checkViteServer();
  if (!viteOk) {
    console.error("❌ Viteサーバーが起動していません");
    console.log("\n起動方法:");
    console.log("  cd /home/nixos/bin/src/kuzu/browse");
    console.log("  deno task dev");
    Deno.exit(1);
  }
  console.log("✅ Viteサーバー稼働中");
  
  // RPCサーバー確認
  const rpcOk = await checkRPCServer();
  if (!rpcOk) {
    console.warn("⚠️  RPCサーバーが起動していません");
    console.log("   UIがRPCサーバーに依存する場合は起動してください:");
    console.log("   cd /home/nixos/bin/src/rpc");
    console.log("   deno run -A main.ts");
  } else {
    console.log("✅ RPCサーバー稼働中");
  }
  
  console.log("\n🚀 E2Eテスト実行中...\n");
  
  // テスト実行
  const command = new Deno.Command("deno", {
    args: ["test", "-A", "test/e2e/", ...Deno.args],
    stdout: "inherit",
    stderr: "inherit",
  });
  
  const { code } = await command.output();
  Deno.exit(code);
}

if (import.meta.main) {
  await main();
}
