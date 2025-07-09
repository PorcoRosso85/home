// 競合解決インターフェースと実装

export interface ConflictResolutionContext {
  nodeId: string;
  property: string;
  nodeType: string;
  existingValue?: any;
  existingTimestamp?: number;
}

export interface ConflictResolver {
  shouldApplyUpdate(
    incomingOp: {
      timestamp: number;
      value: any;
      dependsOn: string[];
    },
    context: ConflictResolutionContext
  ): boolean;
}

// Last-Write-Wins実装
export class LastWriteWinsResolver implements ConflictResolver {
  shouldApplyUpdate(incomingOp: { timestamp: number; dependsOn: string[] }, context: ConflictResolutionContext): boolean {
    // 依存関係がある場合は常に適用（順序を保証）
    if (incomingOp.dependsOn.length > 0 && incomingOp.dependsOn.some(depId => depId.startsWith('op-'))) {
      return true;
    }
    
    // タイムスタンプベースの判定
    if (context.existingTimestamp === undefined) {
      return true;
    }
    
    return incomingOp.timestamp > context.existingTimestamp;
  }
}

// 将来の拡張用プレースホルダー
export class FirstWriteWinsResolver implements ConflictResolver {
  shouldApplyUpdate(incomingOp: any, context: ConflictResolutionContext): boolean {
    // 既に値がある場合は拒否
    return context.existingTimestamp === undefined;
  }
}

export class MergeResolver implements ConflictResolver {
  shouldApplyUpdate(incomingOp: any, context: ConflictResolutionContext): boolean {
    // 常に適用（値のマージが必要な場合）
    return true;
  }
}