// tmuxコマンド実行用の型定義

export type TmuxSessionParams = {
  sessionName: string;
  command: string;
  args: string[];
  outputFile?: string;
};

export type TmuxOutputChunk = {
  type: "output";
  data: string;
};

export type TmuxSessionCreated = {
  type: "session_created";
  sessionName: string;
  outputFile: string;
};

export type TmuxSessionError = {
  type: "error";
  errorCode: "SESSION_ERROR" | "OUTPUT_ERROR";
  message: string;
};

export type TmuxMessage = TmuxOutputChunk | TmuxSessionCreated | TmuxSessionError;
