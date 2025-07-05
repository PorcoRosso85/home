/**
 * URL Crawler のデフォルト設定値
 * ハードコード値の禁止に従い、外部変数として定義
 */

export const DEFAULT_CONCURRENCY = 3;
export const DEFAULT_SAME_HOST = true;
export const DEFAULT_DEPTH = -1; // unlimited
export const DEFAULT_TIMEOUT = 120000; // 2 minutes
export const DEFAULT_RETRIES = 0;
export const DEFAULT_RETRY_DELAY = 1000; // 1 second

// HTTP関連
export const CONTENT_TYPE_HTML = "text/html";
export const USER_AGENT = "URL-Crawler/1.0";

// 出力形式
export const FORMAT_TEXT = "text";
export const FORMAT_JSON = "json";