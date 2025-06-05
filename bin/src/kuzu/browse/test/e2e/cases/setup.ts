/**
 * E2Eテスト共通セットアップ
 * CONVENTION準拠: デフォルト引数禁止
 */

import puppeteer from "npm:puppeteer-core@23.1.0";

export const VITE_URL = "http://localhost:5173";
export const CHROMIUM_PATH = "/home/nixos/.nix-profile/bin/chromium";

/**
 * ブラウザインスタンスを作成
 */
export async function createBrowser(options: {
  headless: boolean;
  chromiumPath: string;
}) {
  return await puppeteer.launch({
    executablePath: options.chromiumPath,
    headless: options.headless,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });
}

/**
 * テスト前提条件の確認
 */
export async function checkPrerequisites(): Promise<void> {
  // Viteサーバー確認
  try {
    const response = await fetch(VITE_URL);
    if (!response.ok) {
      throw new Error(`Vite server returned ${response.status}`);
    }
  } catch (error) {
    throw new Error(
      `Vite開発サーバーが起動していません。\n` +
      `起動方法: cd /home/nixos/bin/src/kuzu/browse && deno run -A build.ts\n` +
      `エラー: ${error instanceof Error ? error.message : String(error)}`
    );
  }
  
  // RPCサーバー確認（警告のみ）
  try {
    const ws = new WebSocket("ws://localhost:8080");
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        ws.close();
        reject(new Error("timeout"));
      }, 1000);
      
      ws.onopen = () => {
        clearTimeout(timeout);
        ws.close();
        resolve();
      };
      
      ws.onerror = () => {
        clearTimeout(timeout);
        reject(new Error("connection error"));
      };
    });
  } catch {
    console.warn(
      "⚠️  RPCサーバーが起動していません。\n" +
      "   UIがRPCサーバーに依存する場合は起動してください:\n" +
      "   cd /home/nixos/bin/src/rpc && deno run -A main.ts"
    );
  }
}

/**
 * テスト用のブラウザオプションを取得
 */
export function getBrowserOptions(): {
  headless: boolean;
  chromiumPath: string;
} {
  return {
    headless: Deno.env.get("HEADLESS") !== "false",
    chromiumPath: Deno.env.get("CHROMIUM_PATH") || CHROMIUM_PATH
  };
}
