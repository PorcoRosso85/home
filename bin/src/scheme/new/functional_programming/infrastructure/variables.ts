/**
 * variables.ts
 * 
 * アプリケーション全体で共有される定数値を一元管理するファイル
 */

/**
 * JSON Schemaのバージョン関連定数
 */
export const JSON_SCHEMA = {
  /**
   * 使用するJSON Schemaのバージョン
   * 最新バージョンは2020-12
   */
  VERSION: '2020-12',
  
  /**
   * JSON Schemaの$schema値（完全なURI）
   */
  URI: 'https://json-schema.org/draft/2020-12/schema'
};

/**
 * スキーマのデフォルト設定値
 */
export const SCHEMA_DEFAULTS = {
  /**
   * デフォルトのスキーマタイトル
   */
  TITLE: 'Function',
  
  /**
   * デフォルトのスキーマ説明
   */
  DESCRIPTION: '関数型プログラミングのための最適化された関数型メタスキーマ'
};

/**
 * アプリケーション設定
 */
export const APP_CONFIG = {
  /**
   * デフォルトの出力ファイル名
   */
  DEFAULT_OUTPUT_FILE: 'Function__Meta.json'
};
