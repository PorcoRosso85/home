/**
 * 汎用クエリ実行システムの型定義
 * 規約準拠: type定義優先、Tagged Union、汎用記述方式
 */

// 基本的な成功・エラー型（Tagged Union）
type QuerySuccess = {
  status: "success";
  data: any;
};

type ValidationError = {
  status: "validation_error";
  field: string;
  message: string;
  details?: any;
};

type ExecutionError = {
  status: "execution_error";
  code: string;
  message: string;
  query?: string;
};

type TemplateNotFoundError = {
  status: "template_not_found";
  templateName: string;
  message: string;
};

// 共用体型（汎用記述方式）
export type QueryResult = QuerySuccess | ValidationError | ExecutionError | TemplateNotFoundError;

// 依存性注入用の型定義
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

// パターンマッチ用のヘルパー型
export type ResultMatcher<T> = {
  success: (data: any) => T;
  validation_error: (error: ValidationError) => T;
  execution_error: (error: ExecutionError) => T;
  template_not_found: (error: TemplateNotFoundError) => T;
};
