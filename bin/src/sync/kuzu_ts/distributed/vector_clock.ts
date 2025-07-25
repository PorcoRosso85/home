/**
 * Vector Clock Implementation
 * ベクタークロックによる分散順序付け
 * 
 * Vector clocks provide a way to track causality in distributed systems.
 * Each node maintains a logical clock that increments on local events
 * and tracks the state of other nodes in the system.
 */

export type ClockSnapshot = Record<string, number>;

export class VectorClock {
  private nodeId: string;
  private clocks: Map<string, number>;

  constructor(nodeId: string) {
    this.nodeId = nodeId;
    this.clocks = new Map<string, number>();
    // Initialize local clock to 0
    this.clocks.set(nodeId, 0);
  }

  /**
   * Get the node ID of this clock
   */
  getNodeId(): string {
    return this.nodeId;
  }

  /**
   * Get the clock value for a specific node
   */
  getValue(nodeId: string): number {
    return this.clocks.get(nodeId) || 0;
  }

  /**
   * Increment the local node's clock
   */
  increment(): void {
    const current = this.getValue(this.nodeId);
    this.clocks.set(this.nodeId, current + 1);
  }

  /**
   * Update a specific node's clock value
   */
  update(nodeId: string, value: number): void {
    this.clocks.set(nodeId, value);
  }

  /**
   * Merge another vector clock into this one
   * Takes the maximum value for each node
   */
  merge(other: VectorClock): void {
    // Get all node IDs from the other clock
    for (const [nodeId, value] of other.clocks) {
      const currentValue = this.getValue(nodeId);
      this.clocks.set(nodeId, Math.max(currentValue, value));
    }
  }

  /**
   * Check if this clock happened before another clock
   * Returns true if all values in this clock are <= other clock
   * and at least one value is strictly less
   */
  happenedBefore(other: VectorClock): boolean {
    let hasStrictlyLess = false;
    
    // Check all nodes in this clock
    for (const [nodeId, value] of this.clocks) {
      const otherValue = other.getValue(nodeId);
      if (value > otherValue) {
        return false; // This clock has a higher value
      }
      if (value < otherValue) {
        hasStrictlyLess = true;
      }
    }
    
    // Check nodes that exist only in other clock
    for (const [nodeId, otherValue] of other.clocks) {
      if (!this.clocks.has(nodeId) && otherValue > 0) {
        hasStrictlyLess = true;
      }
    }
    
    return hasStrictlyLess;
  }

  /**
   * Check if two clocks are concurrent (neither happened before the other)
   */
  isConcurrent(other: VectorClock): boolean {
    return !this.happenedBefore(other) && !other.happenedBefore(this);
  }

  /**
   * Check if two clocks are equal
   */
  equals(other: VectorClock): boolean {
    // Get all unique node IDs
    const allNodeIds = new Set([
      ...this.clocks.keys(),
      ...other.clocks.keys()
    ]);
    
    // Check each node ID
    for (const nodeId of allNodeIds) {
      if (this.getValue(nodeId) !== other.getValue(nodeId)) {
        return false;
      }
    }
    
    return true;
  }

  /**
   * Convert clock to a snapshot object
   */
  toSnapshot(): ClockSnapshot {
    const snapshot: ClockSnapshot = {};
    for (const [nodeId, value] of this.clocks) {
      snapshot[nodeId] = value;
    }
    return snapshot;
  }

  /**
   * Create a VectorClock from a snapshot
   */
  static fromSnapshot(nodeId: string, snapshot: ClockSnapshot): VectorClock {
    const clock = new VectorClock(nodeId);
    for (const [nodeId, value] of Object.entries(snapshot)) {
      clock.update(nodeId, value);
    }
    return clock;
  }
}