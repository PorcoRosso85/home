/**
 * ドメイン型定義（CONVENTION.yaml準拠最小構成）
 * 規約: Legacy型完全削除、個別Tagged Union使用
 */

// Re-export core types
export * from './coreTypes';

// Re-export UI types  
export * from './uiTypes';

// Claude解析機能用Tagged Union（規約準拠）
export type ClaudeAnalysisSuccess = {
  status: "success";
  data: string;
};

export type ClaudeAnalysisError = {
  status: "error"; 
  message: string;
};

export type ClaudeAnalysisResult = ClaudeAnalysisSuccess | ClaudeAnalysisError;

export type ClaudeAnalysisRequest = {
  versionId: string;
  prompt: string;
  nodeData: any; // NodeDataは coreTypes から参照
};

// ステータスメッセージ用Tagged Union（規約準拠）
export type StatusMessage = {
  text: string;
  type: 'info' | 'success' | 'error' | 'loading';
};

// Legacy types完全削除完了
// DatabaseResult削除 - CONVENTION.yaml準拠
