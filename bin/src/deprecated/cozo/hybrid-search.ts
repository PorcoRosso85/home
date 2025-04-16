#!/usr/bin/env -S nix run nixpkgs#deno -- run --allow-read --allow-write --allow-run --allow-env --allow-net

import { parse } from "https://deno.land/std/flags/mod.ts";
import { walk } from "https://deno.land/std/fs/walk.ts";
import { join, relative, extname, dirname, basename } from "https://deno.land/std/path/mod.ts";
import { exists } from "https://deno.land/std/fs/exists.ts";
import { ensureDir } from "https://deno.land/std/fs/ensure_dir.ts";

// Cozo DB設定
const DB_PATH = join(Deno.env.get("HOME") || "/home/nixos", ".cache", "hybrid-search", "docs.db");
const COZO_HTTP_URL = "http://localhost:9070"; // CozoDBのHTTPサーバーURL

// 設定
const EMBEDDING_DIM = 384; // all-MiniLM-L6-v2のデフォルト次元数
const DEFAULT_EXTENSIONS = [".md", ".txt", ".js", ".ts", ".py", ".sh", ".html", ".css", ".json"];

// コマンドライン引数の解析
const args = parse(Deno.args, {
  string: ["query", "dir"],
  boolean: ["help", "index", "vector-only", "text-only"],
  default: { 
    dir: "/home/nixos/cozo",
    "vector-weight": 0.6,
    "text-weight": 0.4,
    limit: 10,
  },
  alias: {
    h: "help",
    q: "query",
    d: "dir",
    i: "index",
    l: "limit",
  },
});

// ヘルプメッセージ
if (args.help) {
  console.log(`Hybrid Search - 指定ディレクトリのファイルをハイブリッド検索します

使用法:
  ./hybrid-search.ts [オプション]

オプション:
  -h, --help                このヘルプを表示
  -d, --dir <path>          検索対象のディレクトリ（デフォルト: /home/nixos/cozo）
  -q, --query <text>        検索クエリ
  -i, --index               インデックスを再構築
  --vector-only             ベクトル検索のみ実行
  --text-only               全文検索のみ実行
  --vector-weight <float>   ベクトル検索のスコア重み（デフォルト: 0.6）
  --text-weight <float>     全文検索のスコア重み（デフォルト: 0.4）
  -l, --limit <number>      結果の最大数（デフォルト: 10）

例:
  ./hybrid-search.ts --dir /home/nixos/docs --query "データベース設計" --limit 5
  ./hybrid-search.ts --index  # インデックスの再構築のみ
`);
  Deno.exit(0);
}

// DBディレクトリの作成
await ensureDir(dirname(DB_PATH));

// CozoDBサーバーの状態を確認
async function checkCozoServer(): Promise<boolean> {
  try {
    const response = await fetch(`${COZO_HTTP_URL}/status`);
    if (response.ok) {
      return true;
    }
    return false;
  } catch (e) {
    console.error(`CozoDBサーバーに接続できません: ${e.message}`);
    return false;
  }
}

// CozoDB HTTP APIを使用してクエリを実行する関数
async function execCozoQuery(query: string): Promise<any> {
  console.log("クエリ実行:", query);
  
  try {
    const response = await fetch(`${COZO_HTTP_URL}/text-query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        script: query,
      }),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP Error ${response.status}: ${errorText}`);
    }
    
    const result = await response.json();
    
    if (result.error) {
      throw new Error(`CozoDB Error: ${result.error}`);
    }
    
    return {
      headers: result.headers || [],
      rows: result.rows || [],
    };
  } catch (e) {
    console.error("クエリ実行エラー:", e);
    throw new Error(`CozoDB query failed: ${e.message}`);
  }
}

// Sentence Transformers APIを使用してエンベディングを取得する
// 注：実際の環境では適切なAPIサービスが必要です
async function getEmbedding(text: string): Promise<number[]> {
  // APIがない場合の簡易的なベクトル生成
  try {
    // まず、SentenceTransformers APIを使用してみる
    const response = await fetch("http://localhost:8080/embed", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        texts: [text],
        model: "all-MiniLM-L6-v2"  // または使用したいモデル
      }),
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.embeddings[0];
    }
  } catch (error) {
    console.warn("Embedding APIに接続できません。フォールバックメソッドを使用します: ", error.message);
  }
  
  // APIが利用できない場合のフォールバック: ハッシュベースのベクトル生成
  console.log("ハッシュベースのエンベディングを生成します。");
  const hash = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)));
  const vector = Array.from(hash).slice(0, EMBEDDING_DIM).map(b => (b / 255) * 2 - 1);
  
  // 指定した次元数に調整
  while (vector.length < EMBEDDING_DIM) {
    vector.push(0);
  }
  
  return vector;
}

// ファイルからテキスト内容を抽出する関数
async function extractTextFromFile(filePath: string): Promise<string> {
  try {
    const content = await Deno.readTextFile(filePath);
    return content;
  } catch (e) {
    console.error(`Error reading file ${filePath}: ${e.message}`);
    return "";
  }
}

// JSONファイルから内容を抽出する特別な関数
async function extractTextFromJsonFile(filePath: string): Promise<string> {
  try {
    const content = await Deno.readTextFile(filePath);
    const json = JSON.parse(content);
    
    // JSONオブジェクトからテキストを抽出
    let extractedText = "";
    
    // 各ページの内容を抽出
    for (const [path, data] of Object.entries(json)) {
      if (typeof data === "object" && data !== null) {
        const page = data as any;
        if (page.title) extractedText += page.title + "\n\n";
        if (page.content) extractedText += page.content + "\n\n";
        if (page.url) extractedText += page.url + "\n\n";
      }
    }
    
    return extractedText;
  } catch (e) {
    console.error(`Error processing JSON file ${filePath}: ${e.message}`);
    return "";
  }
}

// ファイルをインデックス化する関数
async function indexFiles(dirPath: string): Promise<void> {
  console.log(`インデックスを構築中... ディレクトリ: ${dirPath}`);
  
  // CozoDBサーバーチェック
  const isServerRunning = await checkCozoServer();
  if (!isServerRunning) {
    console.error("CozoDBサーバーが起動していません。サーバーを起動してから再試行してください。");
    console.error("例: cozod --http-addr 127.0.0.1:9070");
    Deno.exit(1);
  }
  
  // データベーススキーマの設定（既存のインデックスをドロップ）
  try {
    await execCozoQuery(`:drop documents`);
  } catch (e) {
    // テーブルが存在しない場合はエラーを無視
    console.log("既存のテーブルが見つからないか、削除できません。新しいテーブルを作成します。");
  }
  
  // 新しいスキーマを作成
  await execCozoQuery(`
    :create documents {
      id: String, 
      path: String 
      => 
      filename: String,
      extension: String,
      content: String,
      embedding: <F32; ${EMBEDDING_DIM}>
    }
  `);
  
  // ファイルの探索とインデックス化
  let fileCount = 0;
  
  for await (const entry of walk(dirPath, {
    includeDirs: false,
    exts: DEFAULT_EXTENSIONS,
    skip: [/node_modules/, /\.git/],
  })) {
    const filePath = entry.path;
    const relPath = relative(dirPath, filePath);
    const ext = extname(filePath);
    const fileName = basename(filePath);
    
    // ファイルの内容を読み込む
    let content = "";
    if (ext === ".json") {
      content = await extractTextFromJsonFile(filePath);
    } else {
      content = await extractTextFromFile(filePath);
    }
    
    if (!content) continue;
    
    // テキストから埋め込みベクトルを生成
    const embedding = await getEmbedding(content);
    
    // DBにドキュメントを追加
    const id = relPath.replace(/\\/g, "/");
    const embeddingStr = JSON.stringify(embedding);
    
    // 安全なエスケープのためのヘルパー関数
    const escapeString = (str: string) => str.replace(/"/g, '\\"');
    
    // content はトリプルクォートで囲む
    const contentSafe = content.replace(/"""/g, '\\"""');
    
    await execCozoQuery(`
      ?[id, path, filename, extension, content, embedding] <- [["${escapeString(id)}", "${escapeString(filePath)}", "${escapeString(fileName)}", "${ext}", """${contentSafe}""", ${embeddingStr}]]
      :put documents {id, path => filename, extension, content, embedding}
    `);
    
    fileCount++;
    if (fileCount % 5 === 0) {
      console.log(`${fileCount}ファイルをインデックス化しました...`);
    }
  }
  
  console.log(`インデックス化完了。合計${fileCount}ファイルをインデックス化しました。`);
  
  // ベクトル検索インデックスの作成
  await execCozoQuery(`
    ::hnsw create documents:vector_index {
      fields: [embedding],
      dim: ${EMBEDDING_DIM},
      distance: Cosine,
      ef: 64,
      ef_construction: 128,
      m: 16
    }
  `);
  
  // 全文検索インデックスの作成
  await execCozoQuery(`
    ::fts create documents:text_index {
      extractor: content,
      tokenizer: Simple,
      filters: [Lowercase, Stemmer('english'), Stopwords('en')]
    }
  `);
  
  console.log("ベクトル検索と全文検索のインデックスを作成しました。");
}

// ハイブリッド検索を実行する関数
async function search(query: string, options: {
  vectorOnly?: boolean,
  textOnly?: boolean,
  vectorWeight?: number,
  textWeight?: number,
  limit?: number
}): Promise<void> {
  const {
    vectorOnly = false,
    textOnly = false,
    vectorWeight = 0.6,
    textWeight = 0.4,
    limit = 10
  } = options;
  
  console.log(`検索クエリ: "${query}"`);
  
  // CozoDBサーバーチェック
  const isServerRunning = await checkCozoServer();
  if (!isServerRunning) {
    console.error("CozoDBサーバーが起動していません。サーバーを起動してから再試行してください。");
    console.error("例: cozod --http-addr 127.0.0.1:9070");
    Deno.exit(1);
  }
  
  // テーブルの存在チェック
  try {
    await execCozoQuery(":list");
  } catch (e) {
    console.error("CozoDBのテーブルにアクセスできません。まずインデックスを構築してください。");
    console.error("例: ./hybrid-search.ts --index");
    Deno.exit(1);
  }
  
  // クエリのベクトル埋め込みを取得
  const queryVector = await getEmbedding(query);
  
  let searchQuery = "";
  
  if (vectorOnly) {
    // ベクトル検索のみ
    searchQuery = `
      ?[score, id, path, filename, content] := 
        ~documents:vector_index{id, path, filename, content | 
                              query: ${JSON.stringify(queryVector)}, 
                              bind_score: score,
                              k: ${limit}}
      :order -score
      :limit ${limit}
    `;
  } else if (textOnly) {
    // 全文検索のみ
    searchQuery = `
      ?[score, id, path, filename, content] := 
        ~documents:text_index{id, path, filename, content | 
                           query: "${query.replace(/"/g, '\\"')}", 
                           bind_score: score}
      :order -score
      :limit ${limit}
    `;
  } else {
    // ハイブリッド検索
    searchQuery = `
      vec_results[id, path, filename, content, vec_score] := 
        ~documents:vector_index{id, path, filename, content | 
                              query: ${JSON.stringify(queryVector)}, 
                              bind_score: vec_score,
                              k: ${limit * 2}}
      
      text_results[id, path, filename, content, text_score] := 
        ~documents:text_index{id, path, filename, content | 
                           query: "${query.replace(/"/g, '\\"')}", 
                           bind_score: text_score}
      
      combined[id, path, filename, content, max(combined_score)] := 
        vec_results[id, path, filename, content, vec_score],
        combined_score = vec_score * ${vectorWeight}
      
      combined[id, path, filename, content, max(combined_score)] := 
        text_results[id, path, filename, content, text_score],
        combined_score = text_score * ${textWeight}
      
      combined[id, path, filename, content, max(combined_score)] := 
        vec_results[id, path, filename, content, vec_score],
        text_results[id, path, filename, content, text_score],
        combined_score = vec_score * ${vectorWeight} + text_score * ${textWeight}
      
      ?[combined_score, id, path, filename, content] := 
        combined[id, path, filename, content, combined_score]
      
      :order -combined_score
      :limit ${limit}
    `;
  }
  
  // 検索の実行
  const result = await execCozoQuery(searchQuery);
  
  // 結果の表示
  if (result && result.rows && result.rows.length > 0) {
    console.log("\n検索結果:");
    console.log("=".repeat(80));
    
    for (let i = 0; i < result.rows.length; i++) {
      const [score, id, path, filename, content] = result.rows[i];
      
      // コンテンツのプレビュー（最大200文字）
      const preview = content.length > 200 
        ? content.substring(0, 200) + "..." 
        : content;
      
      console.log(`\n[${i + 1}] スコア: ${score.toFixed(4)}`);
      console.log(`ファイル: ${filename}`);
      console.log(`パス: ${path}`);
      console.log(`プレビュー:\n${preview.split("\n").slice(0, 5).join("\n")}`);
      console.log("-".repeat(80));
    }
  } else {
    console.log("\n検索結果が見つかりませんでした。");
  }
}

// メイン処理
async function main() {
  // インデックス構築が指定された場合
  if (args.index) {
    await indexFiles(args.dir);
  }
  
  // 検索クエリが指定された場合
  if (args.query) {
    await search(args.query, {
      vectorOnly: args["vector-only"],
      textOnly: args["text-only"],
      vectorWeight: parseFloat(args["vector-weight"]),
      textWeight: parseFloat(args["text-weight"]),
      limit: parseInt(args.limit as any)
    });
  } else if (!args.index) {
    console.log("検索クエリが指定されていません。--query オプションで検索クエリを指定するか、--help でヘルプを表示してください。");
  }
}

// 実行
await main();
