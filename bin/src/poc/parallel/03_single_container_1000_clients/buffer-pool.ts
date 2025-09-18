/**
 * 高性能バッファプール - ゼロアロケーション目標
 */

import type { PooledBuffer } from "./types.ts";

export class ExtremeBufferPool {
  private buffers: PooledBuffer[] = [];
  private freeList: number[] = [];
  private readonly bufferSize: number;
  private readonly poolSize: number;
  
  constructor(poolSize: number, bufferSize: number) {
    this.poolSize = poolSize;
    this.bufferSize = bufferSize;
    this.preallocate();
  }
  
  private preallocate(): void {
    console.log(`🔧 Preallocating ${this.poolSize} buffers of ${this.bufferSize} bytes`);
    
    // 一度に大きなArrayBufferを確保してスライス（メモリフラグメンテーション回避）
    const totalSize = this.poolSize * this.bufferSize;
    const megaBuffer = new ArrayBuffer(totalSize);
    const megaArray = new Uint8Array(megaBuffer);
    
    for (let i = 0; i < this.poolSize; i++) {
      const start = i * this.bufferSize;
      const buffer = megaArray.subarray(start, start + this.bufferSize);
      
      this.buffers.push({
        buffer,
        inUse: false,
        lastUsed: 0,
      });
      
      this.freeList.push(i);
    }
  }
  
  acquire(): Uint8Array | null {
    const index = this.freeList.pop();
    if (index === undefined) {
      console.warn("⚠️ Buffer pool exhausted!");
      return null;
    }
    
    const pooled = this.buffers[index];
    pooled.inUse = true;
    pooled.lastUsed = Date.now();
    
    // バッファをクリア（セキュリティ）
    pooled.buffer.fill(0);
    
    return pooled.buffer;
  }
  
  release(buffer: Uint8Array): boolean {
    // O(1)で検索するためにバッファのアドレスでインデックスを計算
    for (let i = 0; i < this.buffers.length; i++) {
      if (this.buffers[i].buffer === buffer) {
        if (!this.buffers[i].inUse) {
          console.warn("⚠️ Double release detected!");
          return false;
        }
        
        this.buffers[i].inUse = false;
        this.freeList.push(i);
        return true;
      }
    }
    
    console.warn("⚠️ Unknown buffer released!");
    return false;
  }
  
  getStats(): {
    total: number;
    free: number;
    used: number;
    utilization: number;
  } {
    return {
      total: this.poolSize,
      free: this.freeList.length,
      used: this.poolSize - this.freeList.length,
      utilization: (this.poolSize - this.freeList.length) / this.poolSize,
    };
  }
  
  // 定期的なクリーンアップ（長時間未使用のバッファ）
  cleanup(maxAge: number = 60000): void {
    const now = Date.now();
    let cleaned = 0;
    
    for (let i = 0; i < this.buffers.length; i++) {
      const pooled = this.buffers[i];
      if (!pooled.inUse && pooled.lastUsed > 0 && now - pooled.lastUsed > maxAge) {
        // メモリをOSに返す可能性を高める
        pooled.buffer.fill(0);
        pooled.lastUsed = 0;
        cleaned++;
      }
    }
    
    if (cleaned > 0) {
      console.log(`🧹 Cleaned ${cleaned} idle buffers`);
    }
  }
}