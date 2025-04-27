// mod.ts - Kuzu-Wasm Denoパッケージのエントリーポイント

// build.tsからメイン関数と開発サーバー作成関数をエクスポート
export { createViteDevServer, main } from "./build.ts";

// 必要に応じてsrc/main.tsからも機能をエクスポート可能
// export * from "./src/main.ts";

// 直接実行された場合、アクセスをログに残すだけ
if (import.meta.main) {
  // 現在のディレクトリ名を取得
  const currentDir = Deno.cwd().split('/').pop();
  console.log(`モジュールが直接実行されました: ${currentDir}/mod.ts`);
  console.log("※ 実際の機能を利用するには、build.tsを直接実行してください:");
  console.log("  deno run -A build.ts");
}

/**
 * Kuzu-Wasm Deno Demo
 * WASMを使用したKuzuグラフデータベースのDenoによる実装例
 * 
 * @example
 * // パッケージとして実行
 * deno run -A -m [現在のディレクトリ名]
 * 
 * // 直接実行
 * deno run -A mod.ts
 */