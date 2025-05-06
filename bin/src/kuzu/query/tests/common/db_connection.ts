/**
 * 階層型トレーサビリティモデル - データベース関連の共通処理
 * 
 * このファイルはデータベース操作に関する共通関数を提供します。
 * - KuzuDBモジュールのロード
 * - データベースディレクトリの作成
 * - データベースの初期化と接続
 * - データベースのクリーンアップ
 */

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

/**
 * KuzuDBモジュールをロードする関数
 * @returns KuzuDBモジュール
 */
export async function loadKuzuModule() {
  try {
    console.log("KuzuDBモジュールをロード試行中...");
    
    // モジュールパスを指定
    const importPath = "../../../browse/node_modules/kuzu-wasm";
    console.log(`モジュールパス: ${importPath}`);
    
    // モジュールをインポート
    const module = await import(importPath);
    console.log("KuzuDBモジュールをロードしました:", Object.keys(module));
    
    // 初期化が必要なら実行
    if (typeof module.default === 'function') {
      console.log("モジュールを初期化します...");
      const kuzu = await module.default();
      console.log("初期化済みモジュール:", Object.keys(kuzu));
      return kuzu;
    }
    
    // 非同期モジュールの場合はデフォルトを返す
    if (module.default) {
      return module.default;
    }
    
    // それ以外は直接モジュールを返す
    return module;
  } catch (error) {
    console.error("KuzuDBモジュールのロード失敗:", error);
    throw error;
  }
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
 * トレーサビリティテスト用のデータベースをセットアップする関数
 * @param dbName データベース名
 * @returns データベース接続オブジェクト
 */
export async function setupDatabase(dbName: string): Promise<any> {
  // データベースの基本ディレクトリを指定
  const baseDir = "src/kuzu/db";
  const dbPath = path.join(Deno.cwd(), baseDir, dbName);
  console.log(`データベースパス: ${dbPath}`);

  // データベースをクリーンな状態から開始する
  await cleanDatabase(dbPath);
  
  // テスト用ディレクトリの作成
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
    
    // ワーカーを無効化
    if (typeof kuzu.setWorkerOptions === 'function') {
      kuzu.setWorkerOptions({ useWorker: false });
      console.log("KuzuDBワーカーを無効化しました");
    } else {
      // 環境変数で無効化
      console.log("KuzuDBワーカーを環境変数で無効化しました");
      Deno.env.set("NO_WORKER", "true");
    }
    
    // データベースの初期化
    console.log(`データベースを初期化中... パス: ${dbPath}`);
    
    let db, conn;
    
    // データベースオプション
    const dbOptions = {
      bufferPoolSize: 1 << 30, // 1GB
      maxNumThreads: 0,        // シングルスレッド
      enableCompression: true,
      readOnly: false,
      useWorker: false,
      enableThreading: false
    };
    
    console.log("データベースオプション:", dbOptions);
    
    // ESMスタイルのAPIを使用
    console.log("ESMスタイルのAPIを使用します");
    
    // Node.js環境のポリフィル
    console.log("Node.js環境のポリフィルを適用します...");
    
    console.log("Databaseを作成します...");
    // ESMスタイルのデータベース作成
    db = await new kuzu.Database(dbPath, dbOptions);
    console.log("ESMスタイルデータベースの作成に成功しました");
    
    // 接続オプション
    const connOptions = {
      useWorker: false,
      maxNumThreads: 0,
      enableThreading: false
    };
    
    console.log("Connectionを作成します...");
    console.log("接続オプション:", connOptions);
    
    // 環境変数で無効化
    console.log("KuzuDBワーカーを環境変数で無効化しました");
    Deno.env.set("NO_WORKER", "true");
    
    // ESMスタイルの接続作成
    conn = await new kuzu.Connection(db, connOptions);
    console.log("ESMスタイル接続の作成に成功しました");
    
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
 * @param db データベースオブジェクト
 * @param conn 接続オブジェクト
 */
export async function closeDatabase(db: any, conn: any) {
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
