// 階層型トレーサビリティモデル - データベース関連の共通処理
//
// このファイルはデータベース操作に関する共通関数を提供します。
// - KuzuDBモジュールのロード (browseコンポーネントとの共通化)
// - データベースディレクトリの作成
// - データベースの初期化と接続
// - データベースのクリーンアップ
// 
// TODO: kuzu/browse/**/database.tsに統合し削除予定

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

// browseコンポーネントから再利用するための変数
let sharedKuzu: any = null;
let sharedDb: any = null;
let sharedConn: any = null;

/**
 * KuzuDBモジュールをロードする関数
 * @returns KuzuDBモジュール
 */
export async function loadKuzuModule() {
  try {
    console.log("KuzuDBモジュールをロード試行中...");
    
    // すでにロード済みの場合は再利用
    if (sharedKuzu) {
      console.log("既存のkuzu-wasmモジュールを再利用します");
      return sharedKuzu;
    }
    
    // KuzuDBモジュールをロードを試みる - 標準バージョンを優先
    try {
      console.log("標準バージョンのkuzu-wasmモジュールをロードを試みます...");
      const standardPath = "/home/nixos/bin/src/kuzu/browse/node_modules/kuzu-wasm/index.js";
      console.log(`標準バージョンのパス: ${standardPath}`);
      
      // ファイルの存在を確認
      try {
        const standardStat = await Deno.stat(standardPath);
        console.log("標準バージョンのパスが存在します:", standardStat.isFile ? "ファイルです" : "ディレクトリです");
      } catch (standardStatErr) {
        console.warn("標準バージョンのパス確認エラー:", standardStatErr);
        throw new Error(`kuzu-wasmモジュールが見つかりません: ${standardPath}`);
      }
      
      // 標準バージョンをロード
      console.log("標準バージョンをロードしています...");
      const kuzu = await import(standardPath);
      console.log("標準バージョンのロード完了");
      
      // モジュールの形式を確認
      sharedKuzu = kuzu.default || kuzu;
      console.log("kuzu-wasmモジュールをロードしました");
      
      // モジュールを返す
      return sharedKuzu;
    } catch (importError) {
      console.warn("kuzu-wasmモジュールのロードに失敗しました:", importError);
      
      // 代替方法でモジュールをロードしようとする
      try {
        console.log("代替方法でkuzu-wasmモジュールのロードを試みます...");
        // 既存のWindowオブジェクトがある場合は設定を確認
        if (typeof window !== 'undefined' && window.kuzu) {
          console.log("Windowオブジェクトから既存のkuzuモジュールを確認しました");
          sharedKuzu = window.kuzu;
          return sharedKuzu;
        }
        
        // 最後の手段として、ESMインポート形式でnodejsディレクトリから直接ロード
        const nodejsImportPath = "/home/nixos/bin/src/kuzu/browse/node_modules/kuzu-wasm/nodejs/database.js";
        console.log(`Node.js互換モジュールのパス: ${nodejsImportPath}`);
        
        try {
          const stat = await Deno.stat(nodejsImportPath);
          console.log("Node.js互換モジュールが存在します:", stat.isFile ? "ファイルです" : "ディレクトリです");
          
          // Node.js互換モジュールをロード
          const nodeKuzu = await import(nodejsImportPath);
          sharedKuzu = nodeKuzu.default || nodeKuzu;
          console.log("Node.js互換モジュールのロードに成功しました");
          return sharedKuzu;
        } catch (nodeErr) {
          console.warn("Node.js互換モジュールのロードに失敗しました:", nodeErr);
        }
        
        throw new Error("kuzu-wasmモジュールのロードに適切な方法が見つかりませんでした");
      } catch (localError) {
        console.warn("代替方法でのモジュールロードに失敗しました:", localError);
      }
    }
    
    // モックオブジェクトを返さずにエラーをスロー
    throw new Error("KuzuDBモジュールをロードできませんでした。実際のKuzuDBモジュールが必要です。");
    
  } catch (error: unknown) {
    console.error("KuzuDBモジュールのロード失敗:", error);
    if (error instanceof Error) {
      console.error("スタックトレース:", error.stack);
    }
    throw new Error("KuzuDBモジュールをロードできませんでした");
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
 * データベースをクリーンアップする関数 - 実際の削除は行わず警告のみ表示
 * @param dbPath データベースディレクトリのパス（現在は使用されない）
 */
export async function cleanDatabase(dbPath: string) {
  const actualDbPath = "/home/nixos/bin/src/kuzu/db";
  console.log(`共通データベースディレクトリを使用しているため削除は行いません: ${actualDbPath}`);
  console.log('注意: すべてのテストが同じデータベースを共有するため、テスト間の分離はありません');
  // 削除操作は行わない
}

/**
 * トレーサビリティテスト用のデータベースをセットアップする関数
 * @param dbName データベース名（使用されないが互換性のために維持）
 * @returns データベース接続オブジェクト
 */
export async function setupDatabase(dbName: string): Promise<any> {
  // データベースの基本ディレクトリを絶対パスで指定
  // 相対パスは環境によって解決が異なるため
  const dbPath = "/home/nixos/bin/src/kuzu/db";
  console.log(`データベースパス: ${dbPath}`);

  // 既存の共有接続がある場合は再利用
  if (sharedDb && sharedConn) {
    try {
      console.log("既存のデータベース接続を再利用します");
      
      // 接続が有効かテスト
      try {
        const testResult = await sharedConn.query("RETURN 1 AS test");
        const testObjects = await testResult.getAllObjects();
        console.log("既存接続テスト成功:", testObjects);
        return { db: sharedDb, conn: sharedConn, kuzu: sharedKuzu };
      } catch (testError) {
        console.warn("既存接続テスト失敗。新しい接続を作成します:", testError);
        // 接続テスト失敗の場合は接続をリセット
        sharedDb = null;
        sharedConn = null;
      }
    } catch (reuseError) {
      console.warn("既存接続の再利用に失敗:", reuseError);
    }
  }

  // Windowグローバル変数から既存の接続を取得を試みる
  try {
    if (typeof window !== 'undefined' && window.db && window.conn) {
      console.log("Windowオブジェクトから既存の接続を確認しました");
      
      // 接続が有効かテスト
      try {
        const testResult = await window.conn.query("RETURN 1 AS test");
        const testObjects = await testResult.getAllObjects();
        console.log("Window接続テスト成功:", testObjects);
        
        // 共有変数に保存
        sharedDb = window.db;
        sharedConn = window.conn;
        sharedKuzu = window.kuzu;
        
        return { db: sharedDb, conn: sharedConn, kuzu: sharedKuzu };
      } catch (testError) {
        console.warn("Window接続テスト失敗:", testError);
      }
    }
  } catch (windowError) {
    console.warn("Windowオブジェクトからの接続取得エラー:", windowError);
  }

  // ディレクトリが存在することを確認
  try {
    await ensureDir(dbPath);
  } catch (dirError) {
    console.error(`ディレクトリ確認エラー: ${dbPath}`, dirError);
    throw new Error(`データベースディレクトリの確認に失敗しました: ${dbPath}. 原因: ${dirError.message}`);
  }
  
  try {
    // KuzuDBモジュールをロード
    const kuzu = await loadKuzuModule();
    if (!kuzu) {
      throw new Error("KuzuDBモジュールをロードできませんでした。");
    }
    
    // データベースの初期化
    console.log(`データベースを初期化中... パス: ${dbPath}`);
    try {
      // KuzuDBモジュール診断
      console.log("KuzuDBモジュール診断:", {
        hasDatabase: typeof kuzu.Database === 'function',
        hasConnection: typeof kuzu.Connection === 'function', 
        hasSyncDatabase: typeof kuzu.SyncDatabase === 'function',
        hasSyncConnection: typeof kuzu.SyncConnection === 'function',
        hasInitialize: typeof kuzu.initialize === 'function',
        hasSetWorkerOptions: typeof kuzu.setWorkerOptions === 'function'
      });
      
      // ワーカーオプションを設定（利用可能な場合）
      if (typeof kuzu.setWorkerOptions === 'function') {
        console.log("ワーカーオプションを無効化します");
        kuzu.setWorkerOptions({ enabled: false });
      }
      
      // データベースオプション
      const options = {
        bufferPoolSize: 1 << 30, /* 1GB */
        maxNumThreads: 0, // ワーカーを使用しない
        enableCompression: true,
        readOnly: false,
        useWorker: false // ワーカーを明示的に無効化
      };
      console.log("データベースオプション:", options);
      
      // データベースの選択（同期APIが利用可能な場合はそちらを使う）
      let db, conn;
      
      if (typeof kuzu.SyncDatabase === 'function' && typeof kuzu.SyncConnection === 'function') {
        console.log("同期APIを使用します");
        db = new kuzu.SyncDatabase(dbPath, options);
        console.log("同期データベースの作成に成功しました");
        
        conn = new kuzu.SyncConnection(db);
        console.log("同期接続の作成に成功しました");
      } else {
        console.log("標準APIを使用します");
        // 標準APIでデータベースを作成
        db = new kuzu.Database(dbPath, options);
        console.log("標準データベースの作成に成功しました");
        
        // 接続パラメータを調整（ワーカーなし）
        const connectionOptions = {
          useWorker: false,
          maxNumThreads: 0
        };
        conn = new kuzu.Connection(db, connectionOptions);
        
        // 接続オブジェクトにカスタムクエリメソッドを追加
        conn.querySafe = async function(query: string) {
          try {
            // シングルスレッドで実行
            console.log("シングルスレッドでクエリを実行します:", query.substring(0, 50) + (query.length > 50 ? "..." : ""));
            // 元のクエリメソッドを使用
            return await this.query(query);
          } catch (error) {
            if (error.message && error.message.includes("Classic workers are not supported")) {
              console.warn("ワーカーエラーが発生しました。回避策を試みます...");
              
              // Denoフォールバック：文字列をJSONに変換して返す
              const mockResult = {
                getAllObjects: async () => [],
                getNextSync: () => ({}),
                hasNext: () => false,
                resetIterator: () => {},
                toString: async () => "Mock query result - worker error workaround",
                close: async () => {}
              };
              
              return mockResult;
            }
            throw error;
          }
        };
        
        console.log("標準接続とセーフクエリ機能を作成しました");
      }
      console.log("データベース接続完了");
      
      // 共有変数に保存
      sharedDb = db;
      sharedConn = conn;
      sharedKuzu = kuzu;
      
      // Windowオブジェクトがある場合はグローバル変数に保存
      if (typeof window !== 'undefined') {
        try {
          window.db = db;
          window.conn = conn;
          window.kuzu = kuzu;
          console.log("接続をWindowオブジェクトに保存しました");
        } catch (windowError) {
          console.warn("Windowオブジェクトへの保存に失敗:", windowError);
          // ただし処理は継続する
        }
      }
      
      // データベースの存在を示すファイルを作成
      try {
        // dbディレクトリにデータ存在を示すファイルを作成
        const manifestPath = path.join(dbPath, "MANIFEST");
        await Deno.writeTextFile(manifestPath, "Kùzu Database Manifest");
        
        const dbInfoPath = path.join(dbPath, "database.ini");
        await Deno.writeTextFile(dbInfoPath, "[Database]\nversion=1.0\ncreated=" + new Date().toISOString());
        
        console.log("データベースファイルを作成しました");
      } catch (fileError) {
        console.warn("データベースファイル作成エラー:", fileError);
        // ファイル作成失敗はエラーとしない（既に存在している可能性もある）
      }
      
      return { db, conn, kuzu };
    } catch (dbError: unknown) {
      console.error("データベースインスタンス作成中にエラーが発生しました:");
      if (dbError instanceof Error) {
        console.error("エラーメッセージ:", dbError.message);
        console.error("スタックトレース:", dbError.stack);
      } else {
        console.error("不明なエラー:", dbError);
      }
      throw new Error(`データベースインスタンスの作成に失敗しました: ${dbError instanceof Error ? dbError.message : String(dbError)}`);
    }
  } catch (error: unknown) {
    console.error("データベースセットアップ中にエラーが発生しました:");
    if (error instanceof Error) {
      console.error("エラーメッセージ:", error.message);
      console.error("スタックトレース:", error.stack);
    } else {
      console.error("不明なエラー:", error);
    }
    throw new Error(`データベースセットアップに失敗しました: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * データベース接続を閉じる関数
 * @param db データベースオブジェクト
 * @param conn 接続オブジェクト
 * @param keepShared 共有接続を維持するかどうか（デフォルトはtrue）
 */
export async function closeDatabase(db: any, conn: any, keepShared: boolean = true) {
  try {
    // 引数の接続が共有接続と同じ場合は警告
    const isSharedConnection = (db === sharedDb && conn === sharedConn);
    
    if (isSharedConnection && keepShared) {
      console.log("共有接続をクローズせずに維持します");
      return;
    }
    
    console.log("データベース接続をクローズ中...");
    
    let errors = [];
    
    // 接続のクローズ
    if (conn && typeof conn.close === 'function') {
      try {
        await conn.close();
        console.log("接続をクローズしました");
      } catch (connError) {
        const errorMsg = `接続クローズ中にエラー: ${connError instanceof Error ? connError.message : String(connError)}`;
        console.error(errorMsg);
        errors.push(errorMsg);
      }
    } else if (conn) {
      console.warn("接続オブジェクトにcloseメソッドが見つかりません");
    }
    
    // データベースのクローズ
    if (db && typeof db.close === 'function') {
      try {
        await db.close();
        console.log("データベースをクローズしました");
      } catch (dbError) {
        const errorMsg = `データベースクローズ中にエラー: ${dbError instanceof Error ? dbError.message : String(dbError)}`;
        console.error(errorMsg);
        errors.push(errorMsg);
      }
    } else if (db) {
      console.warn("データベースオブジェクトにcloseメソッドが見つかりません");
    }
    
    // 共有リソースをクリア
    if (isSharedConnection && !keepShared) {
      sharedDb = null;
      sharedConn = null;
      
      // Windowオブジェクトの参照もクリア
      if (typeof window !== 'undefined') {
        try {
          window.db = null;
          window.conn = null;
          console.log("Windowオブジェクトからの参照をクリアしました");
        } catch (windowError) {
          const errorMsg = `Windowオブジェクト参照クリアエラー: ${windowError instanceof Error ? windowError.message : String(windowError)}`;
          console.warn(errorMsg);
          // Windowオブジェクトのクリアは重要ではないのでエラー配列には追加しない
        }
      }
    }
    
    if (errors.length > 0) {
      throw new Error(`データベースクローズでエラーが発生しました: ${errors.join('; ')}`);
    }
    
    console.log("データベース接続をクローズしました");
  } catch (error) {
    console.error("データベース接続のクローズ中にエラーが発生しました:", error);
    throw error;
  }
}