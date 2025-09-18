import React from "react";
import { renderToString } from "react-dom/server";
import { ensureDir, copy } from "fs/mod.ts";
import { join, dirname } from "path";

// Import page components
import { HomePage } from "./pages/index.tsx";
import { AboutPage } from "./pages/about.tsx";

// Output directory
const OUTPUT_DIR = "./dist";

// Routes configuration (page component and output file path)
const ROUTES = [
  { component: HomePage, path: "index.html" },
  { component: AboutPage, path: "about/index.html" },
];

async function build() {
  console.log("Building static site...");

  // Create output directory
  await ensureDir(OUTPUT_DIR);
  await ensureDir(join(OUTPUT_DIR, "js"));

  // Build each page
  for (const route of ROUTES) {
    const { component, path } = route;
    const outputPath = join(OUTPUT_DIR, path);
    const outputDir = dirname(outputPath);
    
    // Ensure directory exists
    await ensureDir(outputDir);

    // Render the React component to HTML
    const html = "<!DOCTYPE html>\n" + renderToString(React.createElement(component));
    
    // Write the rendered HTML to the output file
    await Deno.writeTextFile(outputPath, html);
    
    console.log(`Generated: ${outputPath}`);
  }

  // Compile TypeScript files to JavaScript
  console.log("Compiling TypeScript files...");
  const tsFiles = [];
  
  // Import our simple transpiler
  const { transformTsToJs } = await import("./transpile.ts");
  
  try {
    for await (const entry of Deno.readDir("./public/js")) {
      if (entry.isFile && entry.name.endsWith(".ts")) {
        tsFiles.push(entry.name);
      }
    }
    
    for (const tsFile of tsFiles) {
      const tsPath = join("./public/js", tsFile);
      const jsFile = tsFile.replace(".ts", ".js");
      const jsPath = join(OUTPUT_DIR, "js", jsFile);
      
      try {
        // 簡易的なアプローチ: 自作の単純なトランスパイラを使用
        const tsContent = await Deno.readTextFile(tsPath);
        
        // 自作のトランスパイラでTypeScriptをJavaScriptに変換
        const jsContent = transformTsToJs(tsContent);
        
        // 生成されたJavaScriptを書き出し
        await Deno.writeTextFile(jsPath, jsContent);
        console.log(`Transpiled: ${tsPath} -> ${jsPath}`);
      } catch (e) {
        console.error(`Error transpiling ${tsPath}:`, e);
        
        // フォールバック: tsをjsにコピーするだけ
        await Deno.copyFile(tsPath, jsPath);
        console.log(`Fallback: Copied ${tsPath} to ${jsPath} instead of transpiling`);
      }
    }
  } catch (error) {
    console.error("Error compiling TypeScript files:", error);
    
    // フォールバック: 全てのTSファイルをJSとしてコピー
    try {
      for await (const entry of Deno.readDir("./public/js")) {
        if (entry.isFile && entry.name.endsWith(".ts")) {
          const tsPath = join("./public/js", entry.name);
          const jsPath = join(OUTPUT_DIR, "js", entry.name.replace(".ts", ".js"));
          await Deno.copyFile(tsPath, jsPath);
          console.log(`Fallback: Copied ${tsPath} to ${jsPath}`);
        }
      }
    } catch (e) {
      console.error("Error in fallback copy:", e);
    }
  }

  // Copy static assets from public directory to output directory
  // Skip .ts files as we've already compiled them
  console.log("Copying static assets...");
  try {
    for await (const entry of Deno.readDir("./public")) {
      if (entry.isFile && !entry.name.endsWith(".ts")) {
        const sourcePath = join("./public", entry.name);
        const destPath = join(OUTPUT_DIR, entry.name);
        await Deno.copyFile(sourcePath, destPath);
        console.log(`Copied: ${sourcePath} -> ${destPath}`);
      } else if (entry.isDirectory && entry.name !== "js") {
        // For directories other than 'js', copy everything
        const sourcePath = join("./public", entry.name);
        const destPath = join(OUTPUT_DIR, entry.name);
        await copy(sourcePath, destPath, { overwrite: true });
        console.log(`Copied directory: ${sourcePath} -> ${destPath}`);
      } else if (entry.isDirectory && entry.name === "js") {
        // For the 'js' directory, copy only non-TS files
        for await (const jsEntry of Deno.readDir(join("./public", "js"))) {
          if (jsEntry.isFile && !jsEntry.name.endsWith(".ts")) {
            const sourcePath = join("./public/js", jsEntry.name);
            const destPath = join(OUTPUT_DIR, "js", jsEntry.name);
            await Deno.copyFile(sourcePath, destPath);
            console.log(`Copied: ${sourcePath} -> ${destPath}`);
          }
        }
      }
    }
  } catch (error) {
    console.error("Error copying static assets:", error);
  }

  console.log("Build completed successfully!");
}

// Run the build
await build();
