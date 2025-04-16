#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-net --allow-read

import { serve } from "https://deno.land/std@0.178.0/http/server.ts";
import { join, dirname, fromFileUrl } from "https://deno.land/std@0.178.0/path/mod.ts";

// パスの計算
const SCRIPT_DIR = dirname(fromFileUrl(import.meta.url));
const INTERFACE_DIR = dirname(SCRIPT_DIR);
const SRC_DIR = dirname(INTERFACE_DIR);
const SCHEME_DIR = dirname(SRC_DIR);

// 絶対パスで指定
const DATA_DIR = "/home/nixos/scheme/data";
const REQUIREMENTS_DIR = "/home/nixos/scheme/data/requirements";

console.log(`SCRIPT_DIR: ${SCRIPT_DIR}`);
console.log(`INTERFACE_DIR: ${INTERFACE_DIR}`);
console.log(`SRC_DIR: ${SRC_DIR}`);
console.log(`SCHEME_DIR: ${SCHEME_DIR}`);
console.log(`DATA_DIR: ${DATA_DIR}`);
console.log(`REQUIREMENTS_DIR: ${REQUIREMENTS_DIR}`);

// サーバー設定
const PORT = 8000;

// 要件ファイル全体を読み込む
async function loadRequirementFiles() {
  try {
    const files = [];
    
    for await (const entry of Deno.readDir(REQUIREMENTS_DIR)) {
      if (entry.isFile && entry.name.endsWith('.json')) {
        const filePath = join(REQUIREMENTS_DIR, entry.name);
        
        try {
          const content = await Deno.readTextFile(filePath);
          const json = JSON.parse(content);
          
          // 必要な情報だけを抽出
          files.push({
            fileName: entry.name,
            id: json.id || '',
            title: json.title || '',
            outputPath: json.outputPath?.default || '',
            implementationType: json.implementationType || ''
          });
        } catch (error) {
          console.error(`Error reading ${entry.name}:`, error);
          files.push({
            fileName: entry.name,
            error: error.message
          });
        }
      }
    }
    
    return files;
  } catch (error) {
    console.error("Error loading requirement files:", error);
    return [];
  }
}

// 出力パスからディレクトリツリーを構築
function buildDirectoryTree(files) {
  // ルートディレクトリを作成
  const root = {
    name: "/",
    type: "directory",
    children: {}
  };
  
  for (const file of files) {
    // 出力パスがない場合はスキップ
    if (!file.outputPath) continue;
    
    // パスの正規化（先頭と末尾のスラッシュを削除）
    let path = file.outputPath;
    if (path.startsWith('/')) {
      path = path.substring(1);
    }
    if (path.endsWith('/')) {
      path = path.slice(0, -1);
    }
    
    // パスを分解
    const parts = path.split('/');
    
    // ファイル名を取得（パスの最後の部分）
    const outputFileName = parts.pop();
    
    // 現在のノードをルートに設定
    let current = root;
    
    // パスの各部分に対してディレクトリを作成
    for (const part of parts) {
      if (!part) continue; // 空の部分はスキップ
      
      // このパス部分のディレクトリが存在しない場合は作成
      if (!current.children[part]) {
        current.children[part] = {
          name: part,
          type: "directory",
          children: {}
        };
      }
      
      // 現在のノードを更新
      current = current.children[part];
    }
    
    // ファイルをこのディレクトリに追加
    if (!current.files) {
      current.files = [];
    }
    
    current.files.push({
      name: outputFileName,
      sourceFile: file.fileName,
      id: file.id,
      title: file.title,
      type: "file"
    });
  }
  
  return root;
}

// ディレクトリツリーをHTMLに変換
function renderDirectoryTree(node, indent = 0) {
  const indentStr = '  '.repeat(indent);
  
  if (node.type === 'file') {
    return `${indentStr}<li class="file" data-source="${node.sourceFile}" data-id="${node.id}">${node.name}</li>\n`;
  }
  
  let html = '';
  
  if (node.name !== '/') {
    html += `${indentStr}<li>\n`;
    html += `${indentStr}  <div class="folder">${node.name}</div>\n`;
    indent += 1;
  }
  
  html += `${indentStr}<ul>\n`;
  
  // ディレクトリを追加
  for (const [name, child] of Object.entries(node.children)) {
    html += renderDirectoryTree(child, indent + 1);
  }
  
  // ファイルを追加
  if (node.files && node.files.length > 0) {
    for (const file of node.files) {
      html += renderDirectoryTree(file, indent + 1);
    }
  } else if (Object.keys(node.children).length === 0) {
    // 空のディレクトリの場合
    html += `${indentStr}  <li class="empty">空のディレクトリ</li>\n`;
  }
  
  html += `${indentStr}</ul>\n`;
  
  if (node.name !== '/') {
    html += `${indentStr}</li>\n`;
  }
  
  return html;
}

// HTML内にデータをエスケープして出力
function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  
  console.log(`Request: ${path}`);
  
  // ファイル一覧とディレクトリツリーを返すAPI
  if (path === "/api/data") {
    return new Promise(async (resolve) => {
      try {
        // 要件ファイルを読み込む
        const files = await loadRequirementFiles();
        
        // ディレクトリツリーを構築
        const tree = buildDirectoryTree(files);
        
        // レスポンスを返す
        resolve(new Response(JSON.stringify({ files, tree }), {
          headers: { "Content-Type": "application/json" }
        }));
      } catch (error) {
        console.error("Error handling request:", error);
        resolve(new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { "Content-Type": "application/json" }
        }));
      }
    });
  }
  
  // ファイル内容を取得するAPI
  if (path.startsWith("/api/file/")) {
    const fileName = path.substring("/api/file/".length);
    
    return new Promise(async (resolve) => {
      try {
        const filePath = join(REQUIREMENTS_DIR, fileName);
        const content = await Deno.readTextFile(filePath);
        
        resolve(new Response(content, {
          headers: { "Content-Type": "application/json" }
        }));
      } catch (error) {
        console.error(`Error reading file ${fileName}:`, error);
        resolve(new Response(JSON.stringify({ error: error.message }), {
          status: 404,
          headers: { "Content-Type": "application/json" }
        }));
      }
    });
  }
  
  // メインページを返す
  if (path === "/" || path === "") {
    return new Promise(async (resolve) => {
      try {
        // 最初にデータを読み込む
        const files = await loadRequirementFiles();
        const tree = buildDirectoryTree(files);
        const treeHtml = renderDirectoryTree(tree);
        
        const html = `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="UTF-8">
            <title>Output Path Tree Viewer</title>
            <style>
              body {
                font-family: sans-serif;
                margin: 0;
                padding: 20px;
                line-height: 1.5;
              }
              .container {
                display: flex;
                height: calc(100vh - 120px);
                border: 1px solid #ccc;
                border-radius: 4px;
              }
              .tree-panel {
                width: 40%;
                padding: 15px;
                overflow: auto;
                border-right: 1px solid #ccc;
                background-color: #f9f9f9;
              }
              .details-panel {
                width: 60%;
                padding: 15px;
                overflow: auto;
              }
              h1 {
                margin-top: 0;
                margin-bottom: 5px;
              }
              h2 {
                margin-top: 0;
                font-size: 1.2em;
              }
              .description {
                color: #666;
                margin-bottom: 20px;
              }
              
              /* ツリースタイル */
              .tree ul {
                list-style-type: none;
                padding-left: 20px;
                margin: 0;
              }
              .tree > ul {
                padding-left: 0;
              }
              .tree li {
                margin: 5px 0;
              }
              .folder {
                cursor: pointer;
                font-weight: bold;
                user-select: none;
              }
              .folder::before {
                content: "📁 ";
              }
              .folder.open::before {
                content: "📂 ";
              }
              .file {
                cursor: pointer;
                color: #0066cc;
              }
              .file::before {
                content: "📄 ";
              }
              .empty {
                color: #999;
                font-style: italic;
              }
              .collapsed {
                display: none;
              }
              
              /* ファイル詳細 */
              .file-details {
                margin-bottom: 20px;
              }
              .file-info {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 15px;
                background-color: #f9f9f9;
              }
              .file-info dl {
                margin: 0;
                display: grid;
                grid-template-columns: 150px auto;
                gap: 5px;
              }
              .file-info dt {
                font-weight: bold;
                color: #555;
              }
              .file-info dd {
                margin: 0;
              }
              .output-path {
                font-family: monospace;
                background-color: #f0f0f0;
                padding: 3px 6px;
                border-radius: 3px;
              }
              .file-content {
                border: 1px solid #ddd;
                border-radius: 4px;
                overflow: auto;
              }
              .file-content pre {
                margin: 0;
                padding: 10px;
              }
              .no-file {
                padding: 20px;
                color: #666;
                text-align: center;
              }
              .error {
                color: #cc0000;
              }
            </style>
          </head>
          <body>
            <h1>Output Path Tree Viewer</h1>
            <p class="description">
              このビューアは、requirements ディレクトリ内のJSONファイルから
              <code>outputPath.default</code> を抽出し、それに基づいたディレクトリ構造を表示します。
            </p>
            
            <div class="container">
              <div class="tree-panel">
                <h2>ディレクトリ構造</h2>
                <div class="tree">
                  ${treeHtml}
                </div>
              </div>
              
              <div class="details-panel">
                <h2>ファイル詳細</h2>
                <div id="file-details" class="file-details">
                  <div class="no-file">
                    左側のツリーからファイルを選択してください
                  </div>
                </div>
              </div>
            </div>
            
            <script>
              // 初期データ
              const files = ${escapeHtml(JSON.stringify(files))};
              
              // ファイル情報を表示
              function displayFileDetails(sourceFile) {
                const fileDetails = document.getElementById('file-details');
                
                // 対応するファイル情報を検索
                const file = files.find(f => f.fileName === sourceFile);
                
                if (!file) {
                  fileDetails.innerHTML = '<div class="error">ファイル情報が見つかりません</div>';
                  return;
                }
                
                if (file.error) {
                  fileDetails.innerHTML = \`
                    <div class="error">
                      <strong>\${file.fileName}</strong>: \${file.error}
                    </div>
                  \`;
                  return;
                }
                
                // ファイル情報を表示
                let html = \`
                  <div class="file-info">
                    <dl>
                      <dt>ファイル名</dt>
                      <dd>\${file.fileName}</dd>
                      
                      <dt>ID</dt>
                      <dd>\${file.id || '<なし>'}</dd>
                      
                      <dt>タイトル</dt>
                      <dd>\${file.title || '<なし>'}</dd>
                      
                      <dt>実装タイプ</dt>
                      <dd>\${file.implementationType || '<なし>'}</dd>
                      
                      <dt>出力パス</dt>
                      <dd>\${file.outputPath ? 
                        \`<span class="output-path">\${file.outputPath}</span>\` : 
                        '<なし>'}</dd>
                    </dl>
                  </div>
                \`;
                
                // ファイル内容を読み込む
                html += \`
                  <h3>ファイル内容</h3>
                  <div class="file-content">
                    <pre id="content-loader">ファイル内容を読み込み中...</pre>
                  </div>
                \`;
                
                fileDetails.innerHTML = html;
                
                // ファイル内容を非同期で読み込む
                loadFileContent(file.fileName);
              }
              
              // ファイル内容を読み込む
              async function loadFileContent(fileName) {
                try {
                  const response = await fetch(\`/api/file/\${fileName}\`);
                  if (!response.ok) {
                    throw new Error(\`APIエラー: \${response.status}\`);
                  }
                  
                  const text = await response.text();
                  
                  try {
                    // JSONとしてパース
                    const data = JSON.parse(text);
                    document.getElementById('content-loader').textContent = 
                      JSON.stringify(data, null, 2);
                  } catch {
                    // JSONとしてパースできない場合はそのまま表示
                    document.getElementById('content-loader').textContent = text;
                  }
                } catch (error) {
                  document.getElementById('content-loader').textContent = 
                    \`エラー: \${error.message}\`;
                }
              }
              
              // フォルダの開閉機能のセットアップ
              function setupFolderToggle() {
                const folders = document.querySelectorAll('.folder');
                
                folders.forEach(folder => {
                  folder.addEventListener('click', (e) => {
                    e.stopPropagation();
                    folder.classList.toggle('open');
                    
                    const ul = folder.nextElementSibling;
                    if (ul && ul.tagName === 'UL') {
                      ul.classList.toggle('collapsed');
                    }
                  });
                  
                  // 初期状態はすべて開いておく
                  folder.classList.add('open');
                });
              }
              
              // ファイルクリックイベントのセットアップ
              function setupFileClick() {
                const fileItems = document.querySelectorAll('.file');
                
                fileItems.forEach(file => {
                  file.addEventListener('click', () => {
                    // 他のファイルの選択状態を解除
                    document.querySelectorAll('.file').forEach(f => {
                      f.classList.remove('selected');
                    });
                    
                    // このファイルを選択状態に
                    file.classList.add('selected');
                    
                    // ファイル詳細を表示
                    displayFileDetails(file.dataset.source);
                  });
                });
              }
              
              // 初期化
              document.addEventListener('DOMContentLoaded', () => {
                setupFolderToggle();
                setupFileClick();
              });
            </script>
          </body>
          </html>
        `;
        
        resolve(new Response(html, {
          headers: { "Content-Type": "text/html" }
        }));
      } catch (error) {
        console.error("Error generating HTML:", error);
        
        // エラーページを返す
        const errorHtml = `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="UTF-8">
            <title>Error</title>
            <style>
              body { font-family: sans-serif; margin: 40px; }
              .error { color: #cc0000; border: 1px solid #cc0000; padding: 20px; border-radius: 4px; }
            </style>
          </head>
          <body>
            <h1>エラーが発生しました</h1>
            <div class="error">
              <p>${error.message}</p>
              <p>${error.stack || ''}</p>
            </div>
          </body>
          </html>
        `;
        
        resolve(new Response(errorHtml, {
          status: 500,
          headers: { "Content-Type": "text/html" }
        }));
      }
    });
  }
  
  // その他のパスは404を返す
  return new Response("404 Not Found", { status: 404 });
}

console.log(`Output Path Tree Viewer - サーバーを起動します on http://localhost:${PORT}/`);
console.log(`REQUIREMENTS_DIR: ${REQUIREMENTS_DIR}`);

serve(handleRequest, { port: PORT });
