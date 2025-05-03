#!/usr/bin/env -S deno run --allow-all

/**
 * KuzuDB WASM永続化テスト
 * 
 * このファイルはKuzuDBのWASM版を使って、kuzu/query/tests/test_db/ディレクトリに
 * データを永続化するテストを実行します。
 * 
 * 実行方法: deno run --allow-all wasm_persistence_test.ts
 */

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

// テストDB用のディレクトリ
const TEST_DB_DIR = "./test_db";

// 現在の作業ディレクトリからの相対パスを絶対パスに変換
const TEST_DB_PATH = path.resolve(Deno.cwd(), TEST_DB_DIR);

// import * as KuzuNativeモジュールをロード
async function loadNativeKuzu() {
  try {
    // Node.jsネイティブモジュールをインポート
    console.log("ネイティブKuzuモジュールをロード試行中...");
    const module = await import("kuzu");
    console.log("ネイティブKuzuモジュールをロードしました、使用可能なメソッド:", Object.keys(module));
    return module;
  } catch (error) {
    console.error("ネイティブKuzuモジュールのロード失敗:", error);
    console.error("スタックトレース:", error.stack);
    return null;
  }
}

async function ensureDir(dir: string): Promise<void> {
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

async function runTest() {
  console.log("KuzuDB 永続化テスト開始");
  console.log(`テストデータベースパス: ${TEST_DB_PATH}`);
  
  // テスト用ディレクトリの作成
  await ensureDir(TEST_DB_PATH);
  
  try {
    // Node.jsネイティブモジュールをロード
    const kuzu = await loadNativeKuzu();

    if (!kuzu) {
      console.error("KuzuDBモジュールをロードできませんでした。テストを中止します。");
      return;
    }
    
    // データベースの初期化
    console.log(`データベースを初期化中... パス: ${TEST_DB_PATH}`);
    const db = new kuzu.Database(TEST_DB_PATH);
    const conn = new kuzu.Connection(db);
    console.log("データベース初期化完了");
    
    // テストデータの作成
    try {
      console.log("テストデータを作成中...");
      
      // ユーザーテーブルの作成
      await conn.query(`
        CREATE NODE TABLE User(
          id INT64, 
          name STRING, 
          email STRING,
          PRIMARY KEY (id)
        )
      `);
      console.log("Userテーブルを作成しました");
      
      // テストデータの挿入
      await conn.query(`CREATE (u:User {id: 1, name: 'Alice', email: 'alice@example.com'})`);
      await conn.query(`CREATE (u:User {id: 2, name: 'Bob', email: 'bob@example.com'})`);
      await conn.query(`CREATE (u:User {id: 3, name: 'Charlie', email: 'charlie@example.com'})`);
      console.log("テストデータを挿入しました");
      
      // データの確認
      const result = await conn.query(`MATCH (u:User) RETURN u.id, u.name, u.email ORDER BY u.id`);
      const rows = await result.getAll();
      console.log("挿入したデータ:", rows);
    } catch (error) {
      console.error("テストデータ作成中にエラーが発生しました:", error);
      // テーブルが既に存在する場合は無視
      if (error.message && error.message.includes("already exists")) {
        console.log("テーブルは既に存在します。既存データを利用します。");
      } else {
        throw error;
      }
    }
    
    // データベース接続をクローズ
    console.log("データベース接続をクローズ中...");
    await conn.close();
    await db.close();
    console.log("データベース接続をクローズしました");
    
    // 接続を切断したデータベースを再読み込みしてデータが永続化されていることを確認
    console.log("永続化の検証のためデータベースを再読み込み中...");
    const verifyDb = new kuzu.Database(TEST_DB_PATH);
    const verifyConn = new kuzu.Connection(verifyDb);
    
    // データの検証
    console.log("永続化されたデータを検証中...");
    const verifyResult = await verifyConn.query(`MATCH (u:User) RETURN u.id, u.name, u.email ORDER BY u.id`);
    const verifyRows = await verifyResult.getAll();
    console.log("永続化されたデータ:", verifyRows);
    
    if (verifyRows.length > 0) {
      console.log("データが正常に永続化されました！");
      console.log(`合計 ${verifyRows.length} 件のレコードが確認されました。`);
    } else {
      console.error("データの永続化に失敗しました。データが見つかりません。");
    }
    
    // 検証用接続のクローズ
    await verifyConn.close();
    await verifyDb.close();
    
  } catch (error) {
    console.error("テスト実行中にエラーが発生しました:", error);
    throw error;
  }
  
  console.log("KuzuDB 永続化テスト完了");
}

// メイン実行部分
if (import.meta.main) {
  runTest()
    .then(() => {
      console.log("テスト成功！");
      Deno.exit(0);
    })
    .catch((error) => {
      console.error("テスト失敗:", error);
      Deno.exit(1);
    });
}

export { runTest };
