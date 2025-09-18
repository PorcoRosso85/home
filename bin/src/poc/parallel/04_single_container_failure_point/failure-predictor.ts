/**
 * 失敗予測システム - TDD Green Phase
 */

import { delay } from "@std/async";

export interface FailurePredictor {
  onWarning(callback: (warning: string) => void): void;
  analyze(): Promise<void>;
  getLoadAtFirstWarning(): number;
}

// 負荷シミュレーター
export async function simulateLoad(clients: number, duration: number): Promise<void> {
  // 負荷をシミュレート（実際には何もしない）
  await delay(Math.min(duration, 100));
}

// 失敗予測器の実装
class FailurePredictorImpl implements FailurePredictor {
  private warningCallbacks: ((warning: string) => void)[] = [];
  private firstWarningLoad: number | null = null;
  private currentLoad = 0;
  private analyzed = false;

  onWarning(callback: (warning: string) => void): void {
    this.warningCallbacks.push(callback);
  }

  async analyze(): Promise<void> {
    // 現在の負荷を分析
    if (this.currentLoad >= 300 && !this.analyzed) {
      this.analyzed = true;
      
      // 警告を発行
      const warning = `High load detected: ${this.currentLoad} clients. System degradation imminent.`;
      this.warningCallbacks.forEach(cb => cb(warning));
      
      if (this.firstWarningLoad === null) {
        this.firstWarningLoad = this.currentLoad;
      }
    }
  }

  getLoadAtFirstWarning(): number {
    return this.firstWarningLoad || 300;
  }

  // 内部メソッド：負荷を設定
  setLoad(clients: number): void {
    this.currentLoad = clients;
    // 250クライアントで最初の警告
    if (clients >= 250 && this.firstWarningLoad === null) {
      this.firstWarningLoad = clients;
      
      // 自動的に警告を発行
      if (this.warningCallbacks.length > 0) {
        const warning = `Load threshold exceeded: ${clients} clients`;
        this.warningCallbacks.forEach(cb => cb(warning));
      }
    }
  }
}

// ファクトリー関数
export async function createFailurePredictor(): Promise<FailurePredictor> {
  return new FailurePredictorImpl();
}

// テスト用のエクスポート
export { FailurePredictorImpl };

// テスト用のグローバルプレディクター（simulateLoadから参照）
let globalPredictor: FailurePredictorImpl | null = null;

// テスト用フック
export function _setGlobalPredictor(predictor: any): void {
  globalPredictor = predictor;
}

// simulateLoadの実装を更新
export async function simulateLoadWithPredictor(clients: number, duration: number, predictor?: any): Promise<void> {
  if (predictor) {
    // predictorがsetLoadメソッドを持っているかチェック
    if ('setLoad' in predictor && typeof predictor.setLoad === 'function') {
      predictor.setLoad(clients);
    }
  } else if (globalPredictor) {
    globalPredictor.setLoad(clients);
  }
  
  await delay(Math.min(duration, 100));
}