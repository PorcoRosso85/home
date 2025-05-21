import { createServer } from "npm:vite@4.5.0";

async function main() {
  try {
    // 最もシンプルな構成
    const server = await createServer({
      // デフォルト設定を使用
      configFile: false, // 設定ファイルは使わない
      root: ".",         // カレントディレクトリをルートとする
    });
    
    await server.listen();
    console.log("サーバー起動完了");
    server.printUrls();
  } catch (error) {
    console.error("エラー:", error);
  }
}

if (import.meta.main) {
  await main();
}
