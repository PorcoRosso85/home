/**
 * File Repository Interface
 * 
 * ファイル操作に関するリポジトリの抽象化
 */

import type { QueryResult } from '../entities/queryResult';

/**
 * ファイルの種類
 */
export type FileType = 'cypher' | 'json' | 'text' | 'binary';

/**
 * ファイル情報
 */
export type FileInfo = {
  path: string;
  name: string;
  size: number;
  type: FileType;
  lastModified: Date;
  exists: boolean;
};

/**
 * ディレクトリ情報
 */
export type DirectoryInfo = {
  path: string;
  files: FileInfo[];
  directories: string[];
  totalSize: number;
};

/**
 * ファイルリポジトリのインターフェース
 */
export type FileRepository = {
  /**
   * ファイルの存在チェック
   */
  exists: (filePath: string) => Promise<boolean> | boolean;
  
  /**
   * ファイルを読み込む
   */
  readFile: (filePath: string, encoding?: BufferEncoding) => Promise<QueryResult<string>> | QueryResult<string>;
  
  /**
   * バイナリファイルを読み込む
   */
  readBinaryFile: (filePath: string) => Promise<QueryResult<Buffer | Uint8Array>> | QueryResult<Buffer | Uint8Array>;
  
  /**
   * ファイルに書き込む
   */
  writeFile: (filePath: string, content: string, encoding?: BufferEncoding) => Promise<QueryResult<void>> | QueryResult<void>;
  
  /**
   * ファイル情報を取得する
   */
  getFileInfo: (filePath: string) => Promise<QueryResult<FileInfo>> | QueryResult<FileInfo>;
  
  /**
   * ディレクトリ内のファイル一覧を取得する
   */
  listDirectory: (directoryPath: string) => Promise<QueryResult<DirectoryInfo>> | QueryResult<DirectoryInfo>;
  
  /**
   * ディレクトリを作成する
   */
  createDirectory: (directoryPath: string) => Promise<QueryResult<void>> | QueryResult<void>;
  
  /**
   * ファイルやディレクトリを削除する
   */
  delete: (path: string) => Promise<QueryResult<void>> | QueryResult<void>;
};

/**
 * ファイル検索オプション
 */
export type FileSearchOptions = {
  /**
   * 拡張子フィルター
   */
  extensions?: string[];
  
  /**
   * ファイル名パターン（正規表現）
   */
  namePattern?: RegExp;
  
  /**
   * 再帰的に検索するか
   */
  recursive?: boolean;
  
  /**
   * 隠しファイルを含むか
   */
  includeHidden?: boolean;
  
  /**
   * 最大ディレクトリ深度
   */
  maxDepth?: number;
};

/**
 * 拡張ファイルリポジトリのインターフェース
 */
export type ExtendedFileRepository = FileRepository & {
  /**
   * 複数ファイルの同時読み込み
   */
  readMultipleFiles: (filePaths: string[]) => Promise<QueryResult<Record<string, string>>>;
  
  /**
   * ファイルの検索
   */
  searchFiles: (basePath: string, options: FileSearchOptions) => Promise<QueryResult<FileInfo[]>>;
  
  /**
   * ファイルのコピー
   */
  copyFile: (sourcePath: string, destinationPath: string) => Promise<QueryResult<void>>;
  
  /**
   * ファイルの移動
   */
  moveFile: (sourcePath: string, destinationPath: string) => Promise<QueryResult<void>>;
  
  /**
   * ファイルのウォッチング
   */
  watchFile: (filePath: string, callback: (event: 'change' | 'delete', filePath: string) => void) => () => void;
  
  /**
   * ファイルの圧縮・解凍
   */
  compressFile: (filePath: string, outputPath: string) => Promise<QueryResult<void>>;
  decompressFile: (filePath: string, outputPath: string) => Promise<QueryResult<void>>;
};

/**
 * ファイル操作のイベント
 */
export type FileEvent = {
  type: 'created' | 'modified' | 'deleted' | 'renamed';
  path: string;
  oldPath?: string; // renameの場合
  timestamp: Date;
};

/**
 * ファイルシステムイベントリスナー
 */
export type FileSystemEventListener = (event: FileEvent) => void;

/**
 * ファイルシステムウォッチャー
 */
export type FileSystemWatcher = {
  /**
   * イベントリスナーを追加
   */
  addEventListener: (listener: FileSystemEventListener) => void;
  
  /**
   * イベントリスナーを削除
   */
  removeEventListener: (listener: FileSystemEventListener) => void;
  
  /**
   * ウォッチングを停止
   */
  stop: () => void;
};
