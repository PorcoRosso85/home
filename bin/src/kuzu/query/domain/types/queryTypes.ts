/**
 * 簡素化されたクエリ実行システムの型定義
 * 規約準拠: type定義優先、Tagged Union（簡素版）、汎用記述方式
 */

// 成功型
type QuerySuccess = {
  success: true;
  data: any;
  templateType?: string;
};

// エラー型（統一）
type QueryError = {
  success: false;
  error: string;
  code?: string;
  templateName?: string;
};

// 共用体型（簡素化版）
export type QueryResult = QuerySuccess | QueryError;

// 依存性注入用の型定義（保持）
export type QueryDependencies = {
  repository: {
    executeQuery: (connection: any, queryName: string, params: any) => Promise<any>;
  };
  templateLoader: {
    load: (templateName: string) => string | null;
    exists: (templateName: string) => boolean;
    scan: (directory: string) => string[];
  };
  logger: {
    info: (message: string, meta?: any) => void;
    error: (message: string, error?: any) => void;
  };
};

export type TemplateScannerDependencies = {
  fileSystem: {
    readDir: (path: string) => string[];
    exists: (path: string) => boolean;
    readFile: (path: string) => string;
  };
  logger: {
    info: (message: string, meta?: any) => void;
    error: (message: string, error?: any) => void;
  };
};

// パターンマッチ用ヘルパー関数（規約準拠）
export function isError(result: QueryResult): result is QueryError {
  return !result.success;
}

export function isSuccess(result: QueryResult): result is QuerySuccess {
  return result.success;
}
