// core/types.ts - 共通の型定義

// スキーマ設定の定義
export interface SchemaConfig {
  // スキーマファイルが格納されているベースディレクトリ
  baseDir: string;
  
  // ルートとなるスキーマファイル名
  rootSchema: string;
  
  // スキーマファイルの再帰探索を行うかどうか
  recursiveSearch: boolean;
  
  // 相対パスを使用するかどうか
  useRelativePaths: boolean;
  
  // デバッグモード
  debug: boolean;
}

// スキーマキャッシュの型定義
export interface SchemaCache {
  [key: string]: any;
}

// 依存関係のマップ型定義
export interface DependencyMap {
  [filePath: string]: string[];
}

// ファイルシステムのインターフェース
export interface FileSystem {
  readTextFile(path: string): Promise<string>;
  writeTextFile(path: string, content: string): Promise<void>;
  exists(path: string): Promise<boolean>;
  listDir(path: string): Promise<FileEntry[]>;
}

// パスユーティリティのインターフェース
export interface PathUtils {
  join(...paths: string[]): string;
  dirname(path: string): string;
  relative(from: string, to: string): string;
  extname(path: string): string;
  basename(path: string): string;
}

// ファイルエントリの型定義
export interface FileEntry {
  name: string;
  path: string;
  isDirectory: boolean;
  isFile: boolean;
}
