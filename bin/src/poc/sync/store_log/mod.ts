// 公開APIのエクスポート

export type {
  EventLogConfig,
  EventLogReader,
  EventLogWriter,
  EventLogPersistence as IEventLogPersistence,
  CausalOperation
} from "./types.ts";

export { FileEventLogPersistence as EventLogPersistence } from "./adapters.ts";

// コア機能は必要に応じて公開
export {
  createEventLine,
  parseEventLine,
  parseEventLines,
  calculateOffset
} from "./core.ts";