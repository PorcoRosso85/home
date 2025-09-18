// platform/deno/fileSystem.ts - Deno向けのファイルシステム実装

import { FileSystem, FileEntry } from '../../core/types.ts';
import { join } from "https://deno.land/std/path/mod.ts";

/**
 * Deno用のファイルシステム実装
 */
export const denoFileSystem: FileSystem = {
  /**
   * ファイルの内容をテキストとして読み込む
   */
  async readTextFile(path: string): Promise<string> {
    return await Deno.readTextFile(path);
  },
  
  /**
   * テキストをファイルに書き込む
   */
  async writeTextFile(path: string, content: string): Promise<void> {
    await Deno.writeTextFile(path, content);
  },
  
  /**
   * ファイルやディレクトリが存在するか確認
   */
  async exists(path: string): Promise<boolean> {
    try {
      await Deno.stat(path);
      return true;
    } catch {
      return false;
    }
  },
  
  /**
   * ディレクトリの内容をリストアップ
   */
  async listDir(path: string): Promise<FileEntry[]> {
    const entries: FileEntry[] = [];
    
    try {
      for await (const entry of Deno.readDir(path)) {
        entries.push({
          name: entry.name,
          path: join(path, entry.name),
          isDirectory: entry.isDirectory,
          isFile: entry.isFile
        });
      }
    } catch (error) {
      console.error(`ディレクトリの読み取りに失敗: ${path}`, error);
    }
    
    return entries;
  }
};
