/**
 * 設定変数
 * 
 * このモジュールでは、アプリケーション全体で使用される設定変数を定義します。
 */

import * as path from 'path';

// データベースパスをシンボリックリンクしたtest_dbディレクトリに設定
export const DB_DIR = "/test_db";  // publicディレクトリ内のシンボリックリンク