/**
 * PathHandlingService.ts
 * 
 * パス操作を行うアプリケーションレベルのサービス
 * 実行環境に依存しない絶対パス解決機能を提供します
 */

import { join, normalize, resolve, dirname } from 'https://deno.land/std/path/mod.ts';

/**
 * パス操作のためのサービスクラス
 */
export class PathHandlingService {
  /**
   * パスを正規化して絶対パスに解決する
   * 
   * @param path 解決するパス
   * @returns 正規化された絶対パス
   */
  resolvePath(path: string): string {
    // 既に絶対パスならそのまま正規化
    if (path.startsWith('/')) {
      return normalize(path);
    }
    
    // 実行環境のカレントディレクトリを取得
    const cwd = Deno.cwd();
    
    // 相対パスを絶対パスに解決
    return resolve(cwd, path);
  }

  /**
   * URLからファイルパスを取得する
   * 
   * @param url ファイルURL
   * @returns 解決されたファイルパス
   */
  fileUrlToPath(url: string | URL): string {
    // URLインスタンスに変換
    const fileUrl = url instanceof URL ? url : new URL(url);
    
    // プロトコルがfile:でない場合はエラー
    if (fileUrl.protocol !== 'file:') {
      throw new Error(`URLはfile:プロトコルである必要があります: ${url}`);
    }
    
    // パスを正規化して返す
    return normalize(fileUrl.pathname);
  }

  /**
   * ファイルのディレクトリパスを取得する
   * 
   * @param filePath ファイルパス
   * @returns ディレクトリパス
   */
  getDirectoryPath(filePath: string): string {
    return dirname(filePath);
  }

  /**
   * 現在のモジュールからの相対パスを絶対パスに解決する
   * 
   * @param moduleUrl 現在のモジュールのURL (通常は import.meta.url)
   * @param relativePath 相対パス
   * @returns 絶対パス
   */
  resolveRelativeToModule(moduleUrl: string | URL, relativePath: string): string {
    // モジュールのパスを取得
    const modulePath = this.fileUrlToPath(moduleUrl);
    const moduleDir = this.getDirectoryPath(modulePath);
    
    // 相対パスを絶対パスに解決
    return join(moduleDir, relativePath);
  }
}
