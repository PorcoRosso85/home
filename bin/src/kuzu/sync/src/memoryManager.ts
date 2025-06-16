/**
 * Memory Manager for Node.js environment
 * Monitors memory usage and manages history pruning
 */

import { EventEmitter } from 'events';

// Type definitions
type MemoryUsage = {
  rss: number;        // Resident Set Size
  heapTotal: number;  // Total size of the allocated heap
  heapUsed: number;   // Actual memory used during execution
  external: number;   // Memory usage of C++ objects bound to JavaScript
  arrayBuffers: number; // Memory allocated for ArrayBuffers and SharedArrayBuffers
};

type MemoryThresholds = {
  heapUsedMB: number;   // Threshold for heap usage in MB
  rssMB: number;        // Threshold for RSS in MB
};

type PruneOptions = {
  keepLatest: number;   // Number of latest entries to keep
  minAge?: number;      // Minimum age in milliseconds
};

type HistoryEntry = {
  id: string;
  timestamp: number;
  data: any;
};

// For test compatibility
type GraphState = {
  nodes: Map<string, any>;
  edges: Map<string, any>;
};

type MemoryManagerConfig = {
  checkInterval?: number;  // Interval for memory checks in ms
  thresholds?: MemoryThresholds;
};

// Memory Manager Interface
interface IMemoryManager {
  startMonitoring(onThresholdExceeded?: (usage: MemoryUsage) => void): void;
  stopMonitoring(): void;
  getMemoryUsage(): MemoryUsage;
  setThreshold(thresholds: MemoryThresholds): void;
  pruneHistory(history: HistoryEntry[], options: PruneOptions): HistoryEntry[];
}

// Create Memory Manager with dependencies
function createMemoryManager(config: MemoryManagerConfig): IMemoryManager {
  let monitoringInterval: NodeJS.Timeout | null = null;
  let thresholds: MemoryThresholds = config.thresholds || {
    heapUsedMB: 512,
    rssMB: 1024
  };
  const checkInterval = config.checkInterval || 5000; // Default: 5 seconds

  // Start monitoring memory usage
  function startMonitoring(onThresholdExceeded?: (usage: MemoryUsage) => void): void {
    if (monitoringInterval) {
      return; // Already monitoring
    }

    monitoringInterval = setInterval(() => {
      const usage = getMemoryUsage();
      
      // Check thresholds
      if (usage.heapUsed > thresholds.heapUsedMB * 1024 * 1024 ||
          usage.rss > thresholds.rssMB * 1024 * 1024) {
        if (onThresholdExceeded) {
          onThresholdExceeded(usage);
        }
      }
    }, checkInterval);
  }

  // Stop monitoring
  function stopMonitoring(): void {
    if (monitoringInterval) {
      clearInterval(monitoringInterval);
      monitoringInterval = null;
    }
  }

  // Get current memory usage
  function getMemoryUsage(): MemoryUsage {
    const usage = process.memoryUsage();
    return {
      rss: usage.rss,
      heapTotal: usage.heapTotal,
      heapUsed: usage.heapUsed,
      external: usage.external,
      arrayBuffers: usage.arrayBuffers
    };
  }

  // Set memory thresholds
  function setThreshold(newThresholds: MemoryThresholds): void {
    thresholds = { ...newThresholds };
  }

  // Prune old history entries
  function pruneHistory(history: HistoryEntry[], options: PruneOptions): HistoryEntry[] {
    // Sort by timestamp (newest first)
    const sorted = [...history].sort((a, b) => b.timestamp - a.timestamp);
    
    // Apply minAge filter if specified
    let filtered = sorted;
    if (options.minAge !== undefined) {
      const cutoffTime = Date.now() - options.minAge;
      filtered = sorted.filter(entry => entry.timestamp >= cutoffTime);
    }
    
    // Keep only the latest N entries
    return filtered.slice(0, options.keepLatest);
  }

  return {
    startMonitoring,
    stopMonitoring,
    getMemoryUsage,
    setThreshold,
    pruneHistory
  };
}

// Export factory function and types
export {
  createMemoryManager
};

export type {
  IMemoryManager,
  MemoryUsage,
  MemoryThresholds,
  PruneOptions,
  HistoryEntry,
  MemoryManagerConfig,
  GraphState
};

// Helper function to format memory usage for logging
export function formatMemoryUsage(usage: MemoryUsage): string {
  const toMB = (bytes: number) => (bytes / 1024 / 1024).toFixed(2);
  
  return [
    `RSS: ${toMB(usage.rss)}MB`,
    `Heap Used: ${toMB(usage.heapUsed)}MB`,
    `Heap Total: ${toMB(usage.heapTotal)}MB`,
    `External: ${toMB(usage.external)}MB`,
    `Array Buffers: ${toMB(usage.arrayBuffers)}MB`
  ].join(', ');
}

// Example usage patterns (for documentation)
/*
// Basic usage
const memoryManager = createMemoryManager({
  checkInterval: 10000, // Check every 10 seconds
  thresholds: {
    heapUsedMB: 256,
    rssMB: 512
  }
});

// Start monitoring with callback
memoryManager.startMonitoring((usage) => {
  console.log('Memory threshold exceeded:', formatMemoryUsage(usage));
  
  // Trigger history pruning or other cleanup
  const prunedHistory = memoryManager.pruneHistory(history, {
    keepLatest: 100,
    minAge: 60000 // Keep entries from last minute
  });
});

// Manual memory check
const currentUsage = memoryManager.getMemoryUsage();
console.log('Current memory:', formatMemoryUsage(currentUsage));

// Update thresholds dynamically
memoryManager.setThreshold({
  heapUsedMB: 384,
  rssMB: 768
});

// Stop monitoring when done
memoryManager.stopMonitoring();
*/