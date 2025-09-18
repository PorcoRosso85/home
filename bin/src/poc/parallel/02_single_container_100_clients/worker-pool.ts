/**
 * ワーカープール実装
 */

import type { WorkerMessage, WorkerResponse } from "./types.ts";

export class Pool {
  private workers: Worker[] = [];
  private taskQueue: Array<{
    resolve: (value: any) => void;
    reject: (error: any) => void;
    method: string;
    args: unknown[];
  }> = [];
  private workerIndex = 0;

  constructor(
    private numWorkers: number,
    private workerPath: string,
  ) {
    this.initializeWorkers();
  }

  private initializeWorkers(): void {
    for (let i = 0; i < this.numWorkers; i++) {
      const worker = new Worker(new URL(this.workerPath, import.meta.url).href, {
        type: "module",
        name: `worker-${i}`,
      });

      worker.onmessage = (e: MessageEvent<WorkerResponse>) => {
        const { id, result, error } = e.data;
        const task = this.taskQueue.find(t => t.method === id);
        
        if (task) {
          if (error) {
            task.reject(new Error(error));
          } else {
            task.resolve(result);
          }
          this.taskQueue = this.taskQueue.filter(t => t !== task);
        }
      };

      worker.onerror = (e) => {
        console.error(`Worker error:`, e);
      };

      this.workers.push(worker);
    }
  }

  async run(method: string, ...args: unknown[]): Promise<any> {
    return new Promise((resolve, reject) => {
      const task = { resolve, reject, method, args };
      this.taskQueue.push(task);
      
      // ラウンドロビンでワーカーを選択
      const worker = this.workers[this.workerIndex];
      this.workerIndex = (this.workerIndex + 1) % this.numWorkers;
      
      const message: WorkerMessage = {
        id: `${method}-${Date.now()}-${Math.random()}`,
        method,
        args,
      };
      
      worker.postMessage(message);
    });
  }

  terminate(): void {
    this.workers.forEach(worker => worker.terminate());
    this.workers = [];
    this.taskQueue = [];
  }
}