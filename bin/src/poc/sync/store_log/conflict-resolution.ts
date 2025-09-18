// Conflict resolution strategy interface
export interface ConflictResolver {
  shouldApplyUpdate(
    incomingUpdate: { timestamp: number; value: any; dependsOn: string[] },
    context: ConflictResolutionContext
  ): boolean;
}

export interface ConflictResolutionContext {
  nodeId: string;
  property: string;
  nodeType: string;
  existingValue?: any;
  existingTimestamp?: number;
}

// Last-Write-Wins (LWW) resolver
export class LastWriteWinsResolver implements ConflictResolver {
  shouldApplyUpdate(
    incomingUpdate: { timestamp: number; value: any; dependsOn: string[] },
    context: ConflictResolutionContext
  ): boolean {
    if (!context.existingTimestamp) {
      return true; // No existing value, apply the update
    }
    return incomingUpdate.timestamp > context.existingTimestamp;
  }
}