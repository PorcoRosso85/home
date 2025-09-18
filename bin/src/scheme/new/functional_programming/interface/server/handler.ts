/**
 * リクエストハンドラー
 * 
 * APIリクエストと静的ファイルリクエストを適切なハンドラーに振り分けます。
 */

import { serveFile } from "https://deno.land/std/http/file_server.ts";
import { extname, join, normalize } from "https://deno.land/std/path/mod.ts";
import { handleApiRequest } from "./apiRouter.ts";

// 設定
// 実行場所に依存しない絶対パスを使用
const SCRIPT_DIR = new URL('.', import.meta.url).pathname;
const PROJECT_ROOT = SCRIPT_DIR.substring(0, SCRIPT_DIR.lastIndexOf('/interface/') + 1);
const BASE_DIR = PROJECT_ROOT; // プロジェクトルートを基準

// フロントエンドディレクトリ（優先順位順）
const FRONTEND_DIRS = ['/dist', '/frontend'];

/**
 * ファイルパスが存在するか確認
 * @param path チェックするパス
 * @returns 存在する場合はtrue
 */
async function fileExists(path: string): Promise<boolean> {
  try {
    const fileInfo = await Deno.stat(path);
    return fileInfo.isFile;
  } catch (_) {
    return false;
  }
}

/**
 * ディレクトリパスが存在するか確認
 * @param path チェックするパス
 * @returns 存在する場合はtrue
 */
async function directoryExists(path: string): Promise<boolean> {
  try {
    const fileInfo = await Deno.stat(path);
    return fileInfo.isDirectory;
  } catch (_) {
    return false;
  }
}

/**
 * 要求されたパスに対して使用するフロントエンドディレクトリを決定
 * @param relativePath 相対パス
 * @returns フロントエンドディレクトリを含む完全なパス
 */
async function resolveFrontendPath(relativePath: string): Promise<string> {
  // 先頭のスラッシュを削除
  const cleanPath = relativePath.startsWith('/') ? relativePath.slice(1) : relativePath;
  
  // 各ディレクトリで存在確認
  for (const dir of FRONTEND_DIRS) {
    const fullPath = join(BASE_DIR, dir.slice(1), cleanPath);
    if (await fileExists(fullPath)) {
      return `${dir}/${cleanPath}`;
    }
  }
  
  // デフォルトはFRONTEND_DIRSの最後のディレクトリを使用
  return `${FRONTEND_DIRS[FRONTEND_DIRS.length - 1]}/${cleanPath}`;
}

// MIMEタイプ
const MIME_TYPES: Record<string, string> = {
  ".html": "text/html",
  ".css": "text/css",
  ".js": "application/javascript",
  ".json": "application/json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".ts": "application/typescript",
};

/**
 * リクエストハンドラー
 * @param req HTTPリクエスト
 * @returns HTTPレスポンス
 */
export async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);
  let path = normalize(url.pathname);
  
  console.log(`${req.method} ${path}`);

  // APIエンドポイント
  if (path.startsWith("/api/")) {
    return handleApiRequest(path, req);
  }

  // ルートパスの場合はindex.htmlにリダイレクト
  if (path === "/" || path === "") {
    path = await resolveFrontendPath("index.html");
  } else {
    // パスのプレフィックスを確認 (既に/frontendや/distで始まっているか)
    const hasValidPrefix = FRONTEND_DIRS.some(dir => path.startsWith(dir));
    
    if (!hasValidPrefix) {
      // 先頭の/を除去して相対パスにする
      const relativePath = path.startsWith('/') ? path.slice(1) : path;
      // フロントエンドディレクトリを自動的に判断
      path = await resolveFrontendPath(relativePath);
    }
  }
  
  console.log(`解決されたパス: ${path}`);

  // 静的ファイルの提供
  try {
    // cwdに依存せず、絶対パスを使用
    const filePath = join(BASE_DIR, path.slice(1));
    console.log(`提供するファイルパス: ${filePath}`);
    const fileInfo = await Deno.stat(filePath);
    
    if (fileInfo.isDirectory) {
      return new Response("ディレクトリアクセスは許可されていません", { status: 403 });
    }
    
    // ファイルを提供
    const response = await serveFile(req, filePath);
    
    // 適切なMIMEタイプを設定
    const ext = extname(filePath).toLowerCase();
    if (ext && MIME_TYPES[ext]) {
      response.headers.set("Content-Type", MIME_TYPES[ext]);
    }
    
    return response;
  } catch (error) {
    console.error(`ファイル提供エラー: ${error instanceof Error ? error.message : String(error)}`);
    return new Response("ファイルが見つかりません", { status: 404 });
  }
}
