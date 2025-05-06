/**
 * 設定変数
 * 
 * このモジュールでは、アプリケーション全体で使用される設定変数を定義します。
 */

import * as path from 'path';

// データベースパスをシンボリックリンクしたdbディレクトリに設定
export const DB_DIR = "/db";  // publicディレクトリ内のシンボリックリンク

// データベース接続設定
export const DB_CONNECTION = {
  // 接続テスト関連
  BASIC_TEST_QUERY: "RETURN 1 AS test",
  CONNECTION_TEST_TIMEOUT_MS: 5000,
  CONNECTION_CHECK_INTERVAL_MS: 30000,
  
  // 再接続関連
  MAX_RETRY_COUNT: 3,
  RETRY_DELAY_MS: 1000,
  
  // キャッシュ関連
  CONNECTION_STATE_CACHE_MS: 10000,  // 接続状態をキャッシュする時間（ミリ秒）
  
  // データベース設定
  DEFAULT_OPTIONS: {
    readOnly: true,           // 公開ディレクトリからのファイルは読み取り専用が安全
    bufferPoolSize: 16 * 1024 * 1024,  // 16MB（最小構成）
    maxNumThreads: 1,         // 最小スレッド数
    enableCompression: false  // 圧縮を無効化（シンプルな構成）
  },
  
  // 必須ファイル（従来の方法）
  REQUIRED_DB_FILES: ['MANIFEST', 'database.ini', 'catalog.kz', 'data.kz', 'metadata.kz'],
  
  // パケットフォーマットファイル（新しい方法）
  PARQUET_FILES_PATH: 'export_data',
  PARQUET_SCRIPT_PATH: 'dql/import.cypher'
};
