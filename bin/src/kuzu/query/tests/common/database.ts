#!/usr/bin/env -S deno run --allow-all

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
    const module = await import("kuzu");
    console.log("KuzuDBモジュールをロードしました、使用可能なメソッド:", Object.keys(module));
    return module;
  } catch (error) {
    console.error("KuzuDBモジュールのロード失敗:", error);
    console.error("スタックトレース:", error.stack);
    return null;
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
  } catch (error) {
    if (!(error instanceof Deno.errors.NotFound)) {
      console.warn(`データベース削除時の警告: ${error.message}`);
    }
  }
}

/**
 * トレーサビリティテスト用のデータベースをセットアップする関数
 * @param dbName データベース名
 * @returns データベース接続オブジェクト
 */
export async function setupDatabase(dbName: string): Promise<any> {
  // データベースの基本ディレクトリ
  const baseDir = "./test_db";
  const dbPath = path.resolve(Deno.cwd(), baseDir, dbName);

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
    
    // データベースの初期化
    console.log(`データベースを初期化中... パス: ${dbPath}`);
    const db = new kuzu.Database(dbPath);
    const conn = new kuzu.Connection(db);
    console.log("データベース初期化完了");
    
    return { db, conn, kuzu };
  } catch (error) {
    console.error("データベースセットアップ中にエラーが発生しました:", error);
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
    await conn.close();
    await db.close();
    console.log("データベース接続をクローズしました");
  } catch (error) {
    console.error("データベース接続のクローズ中にエラーが発生しました:", error);
    throw error;
  }
}
