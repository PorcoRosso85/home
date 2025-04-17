// platform/browser/fileSystem.ts - ブラウザ向けのファイルシステム実装

import { FileSystem, FileEntry } from '../../core/types.ts';

// メモリ内のファイルシステム
const memoryFs: Record<string, string> = {};

/**
 * ブラウザ用のファイルシステム実装（メモリベース）
 */
export const browserFileSystem: FileSystem = {
  /**
   * ファイルの内容をテキストとして読み込む
   */
  async readTextFile(path: string): Promise<string> {
    if (path in memoryFs) {
      return memoryFs[path];
    }
    
    // FileReader APIなどを使った実装に置き換え可能
    throw new Error(`ファイルが見つかりません: ${path}`);
  },
  
  /**
   * テキストをファイルに書き込む
   */
  async writeTextFile(path: string, content: string): Promise<void> {
    // メモリに保存
    memoryFs[path] = content;
  },
  
  /**
   * ファイルやディレクトリが存在するか確認
   */
  async exists(path: string): Promise<boolean> {
    return path in memoryFs;
  },
  
  /**
   * ディレクトリの内容をリストアップ
   * （ブラウザではファイルシステムの概念がないため、メモリ内のファイルを検索）
   */
  async listDir(path: string): Promise<FileEntry[]> {
    const entries: FileEntry[] = [];
    const pathPrefix = path.endsWith('/') ? path : path + '/';
    
    // メモリ内のファイルでパスで始まるものを検索
    for (const filePath of Object.keys(memoryFs)) {
      if (filePath.startsWith(pathPrefix)) {
        const relativePath = filePath.substring(pathPrefix.length);
        const parts = relativePath.split('/');
        const name = parts[0];
        
        // ディレクトリの場合は重複を排除
        if (parts.length > 1) {
          const dirEntry = entries.find(e => e.name === name && e.isDirectory);
          if (!dirEntry) {
            entries.push({
              name,
              path: `${pathPrefix}${name}`,
              isDirectory: true,
              isFile: false
            });
          }
        } else {
          entries.push({
            name,
            path: filePath,
            isDirectory: false,
            isFile: true
          });
        }
      }
    }
    
    return entries;
  }
};

/**
 * Fetchを使用してリモートファイルを取得するファイルシステム
 */
export const fetchFileSystem: FileSystem = {
  /**
   * ファイルの内容をテキストとして読み込む
   */
  async readTextFile(path: string): Promise<string> {
    try {
      const response = await fetch(path);
      if (!response.ok) {
        throw new Error(`HTTP エラー: ${response.status} ${response.statusText}`);
      }
      return await response.text();
    } catch (error: any) {
      throw new Error(`ファイル読み込みに失敗: ${path} - ${error.message}`);
    }
  },
  
  /**
   * テキストをファイルに書き込む（ブラウザでは通常不可）
   */
  async writeTextFile(path: string, content: string): Promise<void> {
    // ブラウザでは通常、サーバーへのPOSTなどを使用
    // ここではメモリに保存
    memoryFs[path] = content;
    
    // FileSaver.jsなどを使用して実際のファイルとしてダウンロードする実装も可能
  },
  
  /**
   * ファイルやディレクトリが存在するか確認
   */
  async exists(path: string): Promise<boolean> {
    if (path in memoryFs) {
      return true;
    }
    
    try {
      const response = await fetch(path, { method: 'HEAD' });
      return response.ok;
    } catch {
      return false;
    }
  },
  
  /**
   * ディレクトリの内容をリストアップ
   * （ブラウザでは通常不可、ディレクトリインデックスのJSONを取得する方法などが必要）
   */
  async listDir(path: string): Promise<FileEntry[]> {
    // メモリ内のファイルを優先して返す
    const entries = await browserFileSystem.listDir(path);
    
    // ディレクトリインデックスJSONを取得する実装も可能
    // 例：fetch(`${path}/index.json`).then(res => res.json())
    
    return entries;
  }
};
