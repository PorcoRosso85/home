/**
 * ドメイン型定義（最小構成）
 * 新しい型は common/types.ts の Result<T> を使用すること
 */

// Re-export core types
export * from './coreTypes';

// Re-export UI types  
export * from './uiTypes';

// Legacy types - 段階的削除予定
export type DatabaseResult = {
  success: boolean;
  data?: any;
  error?: string;
};

export type StatusMessage = {
  text: string;
  type: 'info' | 'success' | 'error' | 'loading';
};

export type ClaudeAnalysisRequest = {
  versionId: string;
  prompt: string;
  nodeData: NodeData;
};

export type ClaudeAnalysisResult = 
  | { status: "success"; data: string }
  | { status: "error"; message: string };

// Import re-exports
import type { NodeData } from './coreTypes';
