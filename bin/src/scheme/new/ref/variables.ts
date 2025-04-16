// スキーマ設定の定義
export const SCHEMA_CONFIG = {
  // スキーマファイルが格納されているベースディレクトリ
  baseDir: "/home/nixos/scheme/new/ref",
  
  // ルートとなるスキーマファイル名（空文字の場合は再帰探索モードになる）
  rootSchema: "",
  
  // スキーマファイルの再帰探索を行うかどうか
  recursiveSearch: true,
  
  // 相対パスを使用するかどうか（trueの場合、出力パスはbaseDirからの相対パスになる）
  useRelativePaths: true,
  
  // 依存関係のグラフをJSON形式で出力するファイル名（空文字の場合は出力しない）
  outputJsonFile: "output.json",
  
  // デバッグモード（詳細情報を表示）
  debug: false
};

// スキーマファイルの拡張子
export const SCHEMA_EXTENSIONS = ['.json'];

// スキーマファイル検索時に除外するディレクトリやファイル
export const EXCLUDE_PATTERNS = [
  'node_modules',
  '.git',
  'dist',
  'build',
  'output.json'
];

// $refキーワードのエイリアス（複数のキーワードを使用可能にする）
export const REF_KEYWORDS = ['$ref'];
