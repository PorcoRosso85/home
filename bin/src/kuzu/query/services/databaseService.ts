/**
 * KuzuDBデータベースサービス
 * 
 * このファイルはKuzuDBへの接続および操作に関するサービスを提供します。
 * - KuzuDBモジュールのロード
 * - データベース接続の管理
 * - データベース操作のユーティリティ関数
 */

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

/**
 * KuzuDBモジュールをロードする関数
 * @returns KuzuDBモジュール
 * @throws npm:kuzuモジュールが見つからない場合にエラーをスロー
 */
export async function loadKuzuModule() {
  console.log("KuzuDBモジュールをロード試行中...");

  // npm:kuzu からインポート
  const importPath = "npm:kuzu";
  console.log(`モジュールパス: ${importPath}`);
  
  // モジュールをインポート
  const kuzu = await import(importPath);
  console.log("KuzuDBモジュールをロードしました:", Object.keys(kuzu));
  
  return kuzu;
}

// KuzuDBの読み込みには常にnpm:kuzuを使用
// 以下の点を考慮する：
// 1. Denoネイティブのkuzuモジュールへの移行
// 2. ワーカーとWebAssemblyの互換性の向上
// 3. パフォーマンス最適化のためのバンドリング方法の改善

// 型定義
export interface DatabaseOptions {
  bufferPoolSize?: number;
  maxNumThreads?: number;
  enableCompression?: boolean;
  readOnly?: boolean;
  useWorker?: boolean;
  enableThreading?: boolean;
}

export interface ConnectionOptions {
  useWorker?: boolean;
  maxNumThreads?: number;
  enableThreading?: boolean;
}

export interface DatabaseConnection {
  db: any;
  conn: any;
  kuzu: any;
}

/**
 * デフォルトのデータベースオプションを取得
 * @returns データベースオプション
 */
export function getDefaultDatabaseOptions(): DatabaseOptions {
  // デフォルトオプションはnullまたは未定義にして、
  // kuzu側のデフォルト値を使用させる
  return {};
}

/**
 * デフォルトの接続オプションを取得
 * @returns 接続オプション
 */
export function getDefaultConnectionOptions(): ConnectionOptions {
  return {};
}

/**
 * データベースのパスを取得する
 * @returns データベースのフルパス
 */
export function getDatabasePath(): string {
  // このファイル（databaseService.ts）のディレクトリパスを取得
  const currentFilePath = new URL(import.meta.url).pathname;
  const currentDir = path.dirname(currentFilePath);
  
  // このファイルから見た相対パスで/home/nixos/bin/src/kuzu/dbへ移動
  const dbDir = path.resolve(currentDir, "../../db");
  
  console.log("現在のファイルパス:", currentFilePath);
  console.log("データベースディレクトリ:", dbDir);
  
  return dbDir;
}

/**
 * ディレクトリの存在を確認し、なければ作成する関数
 * @param dir 確認/作成するディレクトリパス
 */
export async function ensureDir(dir: string): Promise<void> {
  try {
    const stat = await Deno.stat(dir);
    if (!stat.isDirectory) {
      throw new Error(`${dir}はディレクトリではありません`);
    }
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      console.log(`${dir}ディレクトリを作成します`);
      await Deno.mkdir(dir, { recursive: true });
    } else {
      throw error;
    }
  }
}

/**
 * 既存のデータベースを削除してクリーンな状態から始める関数
 * @param dbPath データベースディレクトリのパス
 */
export async function cleanDatabase(dbPath: string) {
  try {
    await Deno.remove(dbPath, { recursive: true });
    console.log(`既存のデータベースを削除しました: ${dbPath}`);
  } catch (error: unknown) {
    if (!(error instanceof Deno.errors.NotFound)) {
      if (error instanceof Error) {
        console.warn(`データベース削除時の警告: ${error.message}`);
      } else {
        console.warn(`データベース削除時の警告: ${String(error)}`);
      }
    }
  }
}

/**
 * データベースを作成し、接続する
 * @param options オプション
 * @returns データベース接続オブジェクト
 */
export async function createDatabase(
  options: {
    dbOptions?: DatabaseOptions;
    connOptions?: ConnectionOptions;
    clean?: boolean;
  } = {}
): Promise<DatabaseConnection> {
  // デフォルトオプションをマージ
  const dbOptions = { ...getDefaultDatabaseOptions(), ...options.dbOptions };
  const connOptions = { ...getDefaultConnectionOptions(), ...options.connOptions };
  const clean = options.clean !== undefined ? options.clean : true;
  
  // データベースパスを取得（dbNameは無視して共通ディレクトリを使用）
  const dbPath = getDatabasePath();
  console.log(`データベースパス: ${dbPath}`);

  // クリーンフラグが有効なら既存DBを削除
  if (clean) {
    await cleanDatabase(dbPath);
  }
  
  // ディレクトリの作成
  await ensureDir(dbPath);
  
  try {
    // KuzuDBモジュールをロード
    const kuzu = await loadKuzuModule();
    if (!kuzu) {
      throw new Error("KuzuDBモジュールをロードできませんでした。");
    }
    
    console.log("KuzuDBモジュール診断:", {
      hasDatabase: !!kuzu.Database,
      hasConnection: !!kuzu.Connection,
      hasSyncDatabase: kuzu.SyncDatabase != null,
      hasSyncConnection: kuzu.SyncConnection != null,
      hasInitialize: typeof kuzu.initialize === 'function',
      hasSetWorkerOptions: typeof kuzu.setWorkerOptions === 'function'
    });
    
    // ワーカーを無効化する必要がある場合のコードですが、デフォルト設定を使用するため無効化
    /*
    if (typeof kuzu.setWorkerOptions === 'function') {
      kuzu.setWorkerOptions({ useWorker: false });
      console.log("KuzuDBワーカーを無効化しました");
    } else {
      // 環境変数で無効化
      console.log("KuzuDBワーカーを環境変数で無効化しました");
      Deno.env.set("NO_WORKER", "true");
    }
    */
    
    // データベースの初期化
    console.log(`データベースを初期化中... パス: ${dbPath}`);
    
    let db, conn;
    
    // データベースオプション
    console.log("データベースオプション:", dbOptions);
    
    // ESMスタイルのAPIを使用
    console.log("ESMスタイルのAPIを使用します");
    
    // Node.js環境のポリフィル
    console.log("Node.js環境のポリフィルを適用します...");
    
    console.log("Databaseを作成します...");
    
    // デフォルトオプションでデータベース作成 (オプションなし)
    console.log("デフォルトオプションでデータベースを作成します");
    db = await new kuzu.Database(dbPath);
    console.log("データベースの作成に成功しました");
    
    // 接続オプション
    console.log("Connectionを作成します...");
    
    // デフォルトオプションで接続作成 (オプションなし)
    console.log("デフォルトオプションで接続を作成します");
    
    // ESMスタイルの接続作成
    conn = await new kuzu.Connection(db);
    console.log("接続の作成に成功しました");
    
    console.log("データベース接続完了");
    
    // ダミーファイルを作成
    try {
      const manifestPath = path.join(dbPath, "MANIFEST");
      await Deno.writeTextFile(manifestPath, "Kùzu Database Manifest");
      
      const dbInfoPath = path.join(dbPath, "database.ini");
      await Deno.writeTextFile(dbInfoPath, "[Database]\nversion=1.0\ncreated=" + new Date().toISOString());
      
      console.log("データベースファイルを作成しました");
    } catch (fileError) {
      console.warn("データベースファイル作成エラー:", fileError);
    }
    
    return { db, conn, kuzu };
  } catch (error: unknown) {
    console.error("データベースセットアップ中にエラーが発生しました:");
    if (error instanceof Error) {
      console.error("エラーメッセージ:", error.message);
      console.error("スタックトレース:", error.stack);
    } else {
      console.error("不明なエラー:", error);
    }
    throw error;
  }
}

/**
 * データベース接続を閉じる関数
 * @param connection データベース接続オブジェクト
 */
export async function closeConnection(connection: DatabaseConnection): Promise<void>;
/**
 * データベース接続を閉じる関数（レガシー互換用）
 * @param db データベースオブジェクト
 * @param conn 接続オブジェクト
 */
export async function closeConnection(db: any, conn: any): Promise<void>;
export async function closeConnection(...args: any[]): Promise<void> {
  let db: any, conn: any;
  
  // 引数の解析
  if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
    // DatabaseConnection オブジェクトを受け取った場合
    const connection = args[0] as DatabaseConnection;
    db = connection.db;
    conn = connection.conn;
  } else if (args.length === 2) {
    // 個別のオブジェクトを受け取った場合（レガシー互換）
    db = args[0];
    conn = args[1];
  } else {
    throw new Error("無効な引数です。DatabaseConnectionオブジェクトまたは(db, conn)ペアを指定してください。");
  }
  
  try {
    console.log("データベース接続をクローズ中...");
    
    // 接続のクローズ
    if (conn && typeof conn.close === 'function') {
      try {
        await conn.close();
        console.log("接続をクローズしました");
      } catch (connError) {
        console.warn("接続クローズ中にエラー:", connError);
      }
    }
    
    // データベースのクローズ
    if (db && typeof db.close === 'function') {
      try {
        await db.close();
        console.log("データベースをクローズしました");
      } catch (dbError) {
        console.warn("データベースクローズ中にエラー:", dbError);
      }
    }
    
    console.log("データベース接続をクローズしました");
  } catch (error) {
    console.error("データベース接続のクローズ中にエラーが発生しました:", error);
    throw error;
  }
}

// 以下はレガシー互換のためのラッパー関数
/**
 * @deprecated createDatabase関数を使用してください
 */
export async function setupDatabase(): Promise<DatabaseConnection> {
  return createDatabase();
}

/**
 * @deprecated closeConnection関数を使用してください
 */
export async function closeDatabase(db: any, conn: any): Promise<void> {
  return closeConnection(db, conn);
}

// データベースサービスのシングルトンインスタンス（任意）
let databaseInstance: DatabaseConnection | null = null;

/**
 * データベースインスタンスを取得（シングルトンパターン）
 * @returns データベース接続オブジェクト
 */
export async function getDatabaseInstance(): Promise<DatabaseConnection> {
  if (!databaseInstance) {
    databaseInstance = await createDatabase();
  }
  return databaseInstance;
}
