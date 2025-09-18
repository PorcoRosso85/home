// 外部依存（インフラストラクチャ層）との接続部

import type { EventLogConfig, EventLogPersistence, CausalOperation } from "./types.ts";
import { createEventLine, parseEventLines, calculateOffset } from "./core.ts";

export class FileEventLogPersistence implements EventLogPersistence {
  private readonly config: EventLogConfig;
  private currentOffset: number = -1;
  private readonly streamControllers = new Set<ReadableStreamDefaultController<CausalOperation>>();
  private lock: Promise<void> = Promise.resolve();

  constructor(config: EventLogConfig) {
    this.config = config;
  }

  async append(event: CausalOperation): Promise<number> {
    // 並行制御のためのロック
    await this.lock;
    let resolveLock: () => void;
    this.lock = new Promise(resolve => { resolveLock = resolve; });

    try {
      const offset = await this.writeEvent(event);
      this.notifyStreams(event);
      return offset;
    } finally {
      resolveLock!();
    }
  }

  async readEvents(fromOffset: number = 0): Promise<CausalOperation[]> {
    const filePath = this.getFilePath();

    try {
      const content = await Deno.readTextFile(filePath);
      const events = parseEventLines(content);
      
      // 現在のオフセットを更新
      this.updateCurrentOffset(content);
      
      return events.slice(fromOffset);
    } catch (error) {
      if (error instanceof Deno.errors.NotFound) {
        return [];
      }
      throw error;
    }
  }

  async getLatestOffset(): Promise<number> {
    if (this.currentOffset >= 0) {
      return this.currentOffset;
    }

    try {
      const content = await Deno.readTextFile(this.getFilePath());
      this.updateCurrentOffset(content);
    } catch (error) {
      if (error instanceof Deno.errors.NotFound) {
        this.currentOffset = -1;
      } else {
        throw error;
      }
    }

    return this.currentOffset;
  }

  stream(): ReadableStream<CausalOperation> {
    return new ReadableStream<CausalOperation>({
      start: (controller) => {
        this.streamControllers.add(controller);
      },
      cancel: () => {
        // cancel時のcontrollerは渡されないため、closeで処理
      }
    });
  }

  async close(): Promise<void> {
    // すべてのストリームを閉じる
    for (const controller of this.streamControllers) {
      try {
        controller.close();
      } catch {
        // 既に閉じている場合は無視
      }
    }
    this.streamControllers.clear();
  }

  private async writeEvent(event: CausalOperation): Promise<number> {
    // ディレクトリを作成
    await Deno.mkdir(this.config.path, { recursive: true });

    const filePath = this.getFilePath();
    const file = await Deno.open(filePath, {
      write: true,
      append: true,
      create: true
    });

    try {
      const line = createEventLine(event);
      const encoder = new TextEncoder();
      await file.write(encoder.encode(line));

      if (this.config.syncWrites) {
        await file.sync();
      }

      this.currentOffset++;
      return this.currentOffset;
    } finally {
      file.close();
    }
  }

  private notifyStreams(event: CausalOperation): void {
    const deadControllers = new Set<ReadableStreamDefaultController<CausalOperation>>();
    
    for (const controller of this.streamControllers) {
      try {
        controller.enqueue(event);
      } catch {
        // コントローラーが既に閉じている場合は削除対象に追加
        deadControllers.add(controller);
      }
    }
    
    // 削除対象のコントローラーを削除
    for (const controller of deadControllers) {
      this.streamControllers.delete(controller);
    }
  }

  private updateCurrentOffset(content: string): void {
    const lines = content.trim().split('\n');
    this.currentOffset = calculateOffset(lines);
  }

  private getFilePath(): string {
    return `${this.config.path}/events.jsonl`;
  }
}