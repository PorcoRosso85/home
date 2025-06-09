/**
 * 環境変数管理
 * build.tsから渡される全ての設定を一元管理
 */

// 環境変数の型定義
export interface EnvironmentVariables {
  LOG_LEVEL: string;
  NODE_ENV: string;
  API_HOST: string;
  API_PORT: string;
  DB_PATH: string;
  KUZU_MOUNTS: Array<{
    source: string;
    target: string;
    pattern?: string;
  }>;
//  // Claude関連設定（最小構成）
  CLAUDE_WS_ENDPOINT: string;
  // Duck API設定
  DUCK_API_HOST: string;
  DUCK_API_PORT: string;
  // DuckLakeクライアント設定
  DUCKLAKE_MAX_RETRIES: string;
  DUCKLAKE_RETRY_DELAY_MS: string;
  DUCKLAKE_CONCURRENT_CONNECTIONS: string;
}

// バリデーションエラー
export class EnvironmentValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'EnvironmentValidationError';
  }
}

// 必須チェック関数
function getRequiredEnv(key: string): string {
  const value = (import.meta as any).env?.[key] || (process as any).env?.[key];
  if (value === undefined || value === null || value === '') {
    throw new EnvironmentValidationError(`Required environment variable '${key}' is not set`);
  }
  return value;
}

// オプショナル取得関数（バリデーション付き）
function getOptionalEnv(key: string, defaultValue: string, validator?: (value: string) => void): string {
  const value = (import.meta as any).env?.[key] || (process as any).env?.[key] || defaultValue;
  if (validator) {
    validator(value);
  }
  return value;
}

// バリデータ関数
const validators = {
  logLevel: (value: string) => {
    const level = parseInt(value);
    if (isNaN(level) || level < 0 || level > 5) {
      throw new EnvironmentValidationError(`Invalid LOG_LEVEL: ${value}. Must be between 0 and 5`);
    }
  },
  
  nodeEnv: (value: string) => {
    const validEnvs = ['development', 'production', 'test'];
    if (!validEnvs.includes(value)) {
      throw new EnvironmentValidationError(`Invalid NODE_ENV: ${value}. Must be one of: ${validEnvs.join(', ')}`);
    }
  },
  
  port: (value: string) => {
    const port = parseInt(value);
    if (isNaN(port) || port < 1 || port > 65535) {
      throw new EnvironmentValidationError(`Invalid port: ${value}. Must be between 1 and 65535`);
    }
  },
  
  host: (value: string) => {
    // 簡易的なホスト名検証
    if (!value || value.length === 0) {
      throw new EnvironmentValidationError(`Invalid host: ${value}. Cannot be empty`);
    }
  },
  
  path: (value: string) => {
    // パスの基本検証
    if (!value || value.length === 0) {
      throw new EnvironmentValidationError(`Invalid path: ${value}. Cannot be empty`);
    }
  },
  
  positiveNumber: (value: string) => {
    const num = parseInt(value);
    if (isNaN(num) || num < 1) {
      throw new EnvironmentValidationError(`Invalid positive number: ${value}. Must be greater than 0`);
    }
  }
};

// 環境変数の取得（バリデーション付き）
export const env: EnvironmentVariables = {
  LOG_LEVEL: getOptionalEnv('LOG_LEVEL', '3', validators.logLevel),
  NODE_ENV: getOptionalEnv('NODE_ENV', 'development', validators.nodeEnv),
  API_HOST: getOptionalEnv('API_HOST', 'localhost', validators.host),
  API_PORT: getOptionalEnv('API_PORT', '3000', validators.port),
  DB_PATH: getOptionalEnv('DB_PATH', './kuzu.db', validators.path),
  // Claude関連設定（最小構成）
  CLAUDE_WS_ENDPOINT: getOptionalEnv('CLAUDE_WS_ENDPOINT', 'ws://localhost:8080'),
  // Duck API設定
  DUCK_API_HOST: getOptionalEnv('DUCK_API_HOST', 'localhost', validators.host),
  DUCK_API_PORT: getOptionalEnv('DUCK_API_PORT', '8000', validators.port),
  // DuckLakeクライアント設定
  DUCKLAKE_MAX_RETRIES: getOptionalEnv('DUCKLAKE_MAX_RETRIES', '3', validators.positiveNumber),
  DUCKLAKE_RETRY_DELAY_MS: getOptionalEnv('DUCKLAKE_RETRY_DELAY_MS', '1000', validators.positiveNumber),
  DUCKLAKE_CONCURRENT_CONNECTIONS: getOptionalEnv('DUCKLAKE_CONCURRENT_CONNECTIONS', '8', validators.positiveNumber),
  KUZU_MOUNTS: (() => {
    try {
      const mounts = (import.meta as any).env?.KUZU_MOUNTS;
      const parsed = mounts ? JSON.parse(mounts) : [];
      
      // マウント設定のバリデーション
      if (!Array.isArray(parsed)) {
        throw new EnvironmentValidationError('KUZU_MOUNTS must be an array');
      }
      
      parsed.forEach((mount, index) => {
        if (!mount.source || !mount.target) {
          throw new EnvironmentValidationError(`Invalid mount at index ${index}: source and target are required`);
        }
      });
      
      return parsed;
    } catch (error) {
      if (error instanceof EnvironmentValidationError) {
        throw error;
      }
      // JSON.parseエラーの場合は空配列を返す
      return [];
    }
  })()
};

// 環境変数の検証は自動的に実行される（getOptionalEnv内で）
// 追加の検証が必要な場合はこの関数を呼ぶ
export function validateEnvironment(): void {
  console.log('Environment validation passed');
  console.log('Configuration:', {
    LOG_LEVEL: env.LOG_LEVEL,
    NODE_ENV: env.NODE_ENV,
    API_HOST: env.API_HOST,
    API_PORT: env.API_PORT,
    DB_PATH: env.DB_PATH,
    KUZU_MOUNTS: env.KUZU_MOUNTS,
    DUCK_API_HOST: env.DUCK_API_HOST,
    DUCK_API_PORT: env.DUCK_API_PORT,
    DUCKLAKE_MAX_RETRIES: env.DUCKLAKE_MAX_RETRIES,
    DUCKLAKE_RETRY_DELAY_MS: env.DUCKLAKE_RETRY_DELAY_MS,
    DUCKLAKE_CONCURRENT_CONNECTIONS: env.DUCKLAKE_CONCURRENT_CONNECTIONS
  });
}
