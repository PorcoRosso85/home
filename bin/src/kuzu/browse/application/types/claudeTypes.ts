/**
 * Claude解析機能専用型定義
 * CONVENTION.yaml準拠: 個別Tagged Union実装
 */

// Claude解析成功型
export type ClaudeAnalysisSuccess = {
  status: "success";
  data: string;
};

// Claude解析エラー型
export type ClaudeAnalysisError = {
  status: "error";
  message: string;
};

// Claude解析結果型（Tagged Union）
export type ClaudeAnalysisResult = ClaudeAnalysisSuccess | ClaudeAnalysisError;

// Claude解析リクエスト型
export type ClaudeAnalysisRequest = {
  versionId: string;
  prompt: string;
  nodeData: any;
};

// Claude RPC クライアント型
export type ClaudeRpcClient = {
  sendClaudeRequest: (prompt: string) => Promise<ClaudeAnalysisResult>;
};
