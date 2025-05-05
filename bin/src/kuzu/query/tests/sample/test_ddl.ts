#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - DDL呼び出しテスト
 * 
 * このファイルはDDL呼び出し機能をテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl, callNamedDdl } from "../call_ddl.ts";

// テスト用DBの名前
const TEST_DB_NAME = "ddl_test_db";

// メイン実行関数
(async () => {
  console.log("===== DDL呼び出しテスト =====");
  
  // 初期化
  let db: any, conn: any;
  
  try {
    // 1. データベースセットアップ
    console.log("\n1. データベースセットアップ");
    const result = await setupDatabase(TEST_DB_NAME);
    db = result.db;
    conn = result.conn;
    console.log("✓ データベースセットアップ完了");
    
    // 2. DDLファ