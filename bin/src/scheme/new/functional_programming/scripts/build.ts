#!/usr/bin/env -S nix-shell -p deno --run deno run --allow-read --allow-write --allow-run
/**
 * build.ts
 * 
 * TypeScriptファイルをJavaScriptにコンパイルし、
 * 必要なファイルをdistディレクトリに配置するビルドスクリプト
 * 
 * 使用方法:
 * ```bash
 * ./scripts/build.ts
 * ```
 */

import * as path from "node:path";
import { ensureDir, copy } from "https://deno.land/std/fs/mod.ts";

// プロジェクトルートパス
const rootDir = path.resolve(Deno.cwd());
const srcDir = path.join(rootDir, "interface");
const distDir = path.join(rootDir, "dist");

/**
 * メインビルド処理
 */
async function build() {
  console.log("ビルドを開始します...");
  
  // distディレクトリの作成/クリーンアップ
  await ensureDir(distDir);
  
  // browser.tsをコンパイル
  console.log("TypeScript → JavaScript コンパイル中...");
  const browserTsPath = path.join(srcDir, "browser.ts");
  const browserJsPath = path.join(distDir, "browser.js");
  
  const buildProcess = Deno.run({
    cmd: [
      "deno", 
      "bundle", 
      "--config", path.join(rootDir, "deno.json"),
      browserTsPath, 
      browserJsPath
    ],
    stdout: "piped",
    stderr: "piped"
  });
  
  const { code } = await buildProcess.status();
  
  if (code !== 0) {
    const stderr = new TextDecoder().decode(await buildProcess.stderrOutput());
    console.error("コンパイルエラー:", stderr);
    Deno.exit(1);
  }
  
  console.log(`コンパイル完了: ${browserJsPath}`);
  
  // HTMLとCSSが既に存在するか確認し、存在しない場合は作成
  const htmlPath = path.join(distDir, "index.html");
  const cssPath = path.join(distDir, "styles.css");
  
  try {
    await Deno.stat(htmlPath);
    console.log("index.html は既に存在します");
  } catch {
    console.log("index.html を作成中...");
    await createIndexHtml(htmlPath);
  }
  
  try {
    await Deno.stat(cssPath);
    console.log("styles.css は既に存在します");
  } catch {
    console.log("styles.css を作成中...");
    await createStylesCss(cssPath);
  }
  
  console.log("ビルドが完了しました！");
  console.log(`ディレクトリ: ${distDir}`);
}

/**
 * index.htmlの作成
 */
async function createIndexHtml(htmlPath: string) {
  const html = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>関数型スキーマビューア</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div id="app"></div>
  <script type="module" src="browser.js"></script>
</body>
</html>
`;
  
  await Deno.writeTextFile(htmlPath, html);
}

/**
 * styles.cssの作成
 */
async function createStylesCss(cssPath: string) {
  const css = `/* styles.css */
:root {
  --primary-color: #3498db;
  --secondary-color: #2c3e50;
  --accent-color: #e74c3c;
  --bg-color: #f8f9fa;
  --panel-bg: white;
  --border-color: #ddd;
  --text-color: #333;
  --link-color: #2980b9;
  --hover-color: #f0f0f0;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.6;
  color: var(--text-color);
  background-color: var(--bg-color);
  margin: 0;
  padding: 0;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 以下略 - 実際のCSSはもっと詳細に記述 */
`;
  
  await Deno.writeTextFile(cssPath, css);
}

// メイン実行
if (import.meta.main) {
  build().catch(err => {
    console.error("ビルドエラー:", err);
    Deno.exit(1);
  });
}
