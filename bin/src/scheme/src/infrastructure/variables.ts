/**
 * 環境変数とアプリケーション定数を管理するモジュール
 * 
 * このファイルは環境変数の読み込みとアプリケーション全体で使用する
 * 定数の中央管理を担当します。
 */

// 環境変数から値を取得する関数
// デフォルト値を指定できる
function getEnv(key: string, defaultValue: string): string {
  // Denoのプロセス環境変数から値を取得
  try {
    const value = Deno.env.get(key);
    return value !== undefined ? value : defaultValue;
  } catch {
    // 環境変数へのアクセスができない場合はデフォルト値を返す
    return defaultValue;
  }
}

// ディレクトリパス関連の定数
export const DIRECTORIES = {
  // ベースディレクトリ
  BASE: getEnv("SCHEME_BASE_DIR", "/home/nixos/scheme"),
  
  // データ関連ディレクトリ
  DATA: getEnv("SCHEME_DATA_DIR", "/home/nixos/scheme/data"),
  
  // 生成されたスキーマの保存先
  GENERATED: getEnv("SCHEME_GENERATED_DIR", "/home/nixos/scheme/data/generated"),
  
  // 統一要件の保存先
  REQUIREMENTS: getEnv("SCHEME_REQUIREMENTS_DIR", "/home/nixos/scheme/data/requirements"),
  
  // メタスキーマの保存先
  META: getEnv("SCHEME_META_DIR", "/home/nixos/scheme/data/meta"),
  
  // 旧形式の設定ファイル格納先（非推奨）
  OLD_CONFIG: getEnv("SCHEME_OLD_CONFIG_DIR", "/home/nixos/scheme/data/config"),
  
  // 旧形式の要件ファイル格納先（非推奨）
  OLD_REQUIREMENTS: getEnv("SCHEME_OLD_REQUIREMENTS_DIR", "/home/nixos/scheme/data/requirements.generated"),
};

// メタスキーマのソースタイプ
export enum META_SOURCE_TYPE {
  LOCAL = 'local',
  WEB = 'web',
  CDN = 'cdn',
  OPFS = 'opfs',
}

// メタスキーマのソース別設定
export const META_SOURCE_CONFIG = {
  [META_SOURCE_TYPE.LOCAL]: {
    BASE_DIR: DIRECTORIES.GENERATED,
  },
  [META_SOURCE_TYPE.WEB]: {
    BASE_URL: getEnv("SCHEME_WEB_BASE_URL", "https://schema-repository.example.com"),
  },
  [META_SOURCE_TYPE.CDN]: {
    BASE_URL: getEnv("SCHEME_CDN_BASE_URL", "https://cdn.schema-repository.example.com"),
  },
  [META_SOURCE_TYPE.OPFS]: {
    BASE_PATH: getEnv("SCHEME_OPFS_BASE_PATH", "/schema"),
  },
};

// スキーマ関連の設定
export const SCHEMA_CONFIG = {
  DEFAULT_SCHEMA_VERSION: "http://json-schema.org/draft-07/schema#",
  URI_SCHEME: "scheme://",
};

// 表示関連の設定
export const DISPLAY_CONFIG = {
  // 依存関係表示のインデント幅
  DEPENDENCY_INDENT_WIDTH: 2,
  // パスと依存関係の区切り文字
  DEPENDENCY_SEPARATOR: "|",
};

// ファイル名パターン
export const FILE_PATTERNS = {
  SCHEMA_JSON: ".schema.json",
  CONFIG_JSON: ".config.json",
  REQUIREMENT_JSON: ".require.json",
  META_JSON: ".meta.json",
};
