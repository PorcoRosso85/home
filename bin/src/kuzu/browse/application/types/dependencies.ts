/**
 * CONVENTION.yaml準拠 依存性注入型定義
 * 規約: 高階関数による依存性注入を活用
 */

// ログ依存性
export type LoggerDependency = {
  debug: (message: string, data?: any) => void;
  info: (message: string, data?: any) => void;
  warn: (message: string, data?: any) => void;
  error: (message: string, error?: any) => void;
};

// クエリ実行依存性
export type QueryExecutorDependency = {
  execute: (connection: any, query: string, params: any) => Promise<any>;
  validate: (query: string) => boolean;
};

// バージョン機能の依存性
export type VersionDependencies = {
  queryExecutor: QueryExecutorDependency;
  logger: LoggerDependency;
};

// LocationURI機能の依存性
export type LocationUriDependencies = {
  queryExecutor: QueryExecutorDependency;
  logger: LoggerDependency;
  versionProgressRepository: any;
  versionCompletionService: any;
};

// Claude解析機能の依存性
export type ClaudeAnalysisDependencies = {
  apiClient: {
    send: (prompt: string, data: any) => Promise<any>;
  };
  logger: LoggerDependency;
};
