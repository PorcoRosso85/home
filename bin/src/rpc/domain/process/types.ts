// プロセス管理の型定義

export type ProcessId = string;

export type ProcessInfo = {
  id: ProcessId;
  command: string;
  args: string[];
  startTime: string; // ISO 8601形式
  status: "running" | "completed" | "error";
};

export type ProcessStartParams = {
  id: ProcessId;
  command: string;
  args: string[];
};

export type ProcessListResult = {
  processes: ProcessInfo[];
};

export type ProcessKillResult = {
  status: "success";
} | {
  status: "error";
  errorCode: "NOT_FOUND" | "KILL_FAILED";
  message: string;
};

export type ProcessManagerConfig = {
  maxConcurrent: number;
};

export type ProcessStore = Map<ProcessId, {
  info: ProcessInfo;
  process: Deno.ChildProcess;
  output: string[];
}>;
