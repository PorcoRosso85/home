// platform/deno/pathUtils.ts - Deno向けのパス操作ユーティリティ実装

import { PathUtils } from '../../core/types.ts';
import { 
  join, 
  dirname, 
  relative, 
  extname, 
  basename 
} from "https://deno.land/std/path/mod.ts";

/**
 * Deno用のパスユーティリティ実装
 */
export const denoPathUtils: PathUtils = {
  /**
   * パスの要素を結合する
   */
  join(...paths: string[]): string {
    return join(...paths);
  },
  
  /**
   * パスの親ディレクトリを取得
   */
  dirname(path: string): string {
    return dirname(path);
  },
  
  /**
   * fromパスからtoパスへの相対パスを取得
   */
  relative(from: string, to: string): string {
    return relative(from, to);
  },
  
  /**
   * ファイルの拡張子を取得
   */
  extname(path: string): string {
    return extname(path);
  },
  
  /**
   * ファイル名を取得
   */
  basename(path: string): string {
    return basename(path);
  }
};
