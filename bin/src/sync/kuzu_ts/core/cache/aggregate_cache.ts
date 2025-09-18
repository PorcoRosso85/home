/**
 * Aggregate Cache Implementation
 * Efficient caching for aggregate operations with O(1) retrieval
 */

import type { TemplateEvent } from "../../event_sourcing/types.ts";

export type AggregateType = "COUNT" | "SUM" | "AVG" | "MIN" | "MAX";

export interface AggregateDefinition {
  name: string;
  type: AggregateType;
  target: string;
  field?: string; // Required for SUM, AVG, MIN, MAX
  predicate?: (event: TemplateEvent) => boolean;
}

interface AggregateEntry {
  definition: AggregateDefinition;
  value: number | null;
  // For AVG, we need to track both sum and count
  metadata?: {
    sum?: number;
    count?: number;
  };
}

export interface AggregateStats {
  aggregateCount: number;
  cacheHits: number;
  cacheMisses: number;
}

export interface AggregateMemoryStats {
  aggregateCount: number;
  estimatedSizeBytes: number;
}

export class AggregateCache {
  private aggregates: Map<string, AggregateEntry>;
  private stats: AggregateStats;

  constructor() {
    this.aggregates = new Map();
    this.stats = {
      aggregateCount: 0,
      cacheHits: 0,
      cacheMisses: 0
    };
  }

  /**
   * Define a new aggregate
   */
  defineAggregate(definition: AggregateDefinition): void {
    const entry: AggregateEntry = {
      definition,
      value: null,
      metadata: definition.type === "AVG" ? { sum: 0, count: 0 } : undefined
    };
    
    this.aggregates.set(definition.name, entry);
    this.stats.aggregateCount++;
  }

  /**
   * Get aggregate value with O(1) access
   */
  getValue(name: string): number | null {
    const entry = this.aggregates.get(name);
    
    if (entry && entry.value !== null) {
      this.stats.cacheHits++;
      return entry.value;
    } else {
      this.stats.cacheMisses++;
      return null;
    }
  }

  /**
   * Set aggregate value directly (for testing or initialization)
   */
  setValue(name: string, value: number): void {
    const entry = this.aggregates.get(name);
    if (entry) {
      entry.value = value;
    }
  }

  /**
   * Process an event and update relevant aggregates
   */
  processEvent(event: TemplateEvent): void {
    for (const [name, entry] of this.aggregates.entries()) {
      const { definition } = entry;
      
      // Check if event matches this aggregate's target
      if (!this.eventMatchesTarget(event, definition.target)) {
        continue;
      }
      
      // Apply predicate if defined
      if (definition.predicate && !definition.predicate(event)) {
        continue;
      }
      
      // Update aggregate based on type
      switch (definition.type) {
        case "COUNT":
          this.updateCount(entry, event);
          break;
        case "SUM":
          this.updateSum(entry, event);
          break;
        case "AVG":
          this.updateAvg(entry, event);
          break;
        case "MIN":
          this.updateMin(entry, event);
          break;
        case "MAX":
          this.updateMax(entry, event);
          break;
      }
    }
  }

  /**
   * Get cache statistics
   */
  getStats(): AggregateStats {
    return { ...this.stats };
  }

  /**
   * Get memory statistics
   */
  getMemoryStats(): AggregateMemoryStats {
    const baseSize = 100; // Base object overhead
    const entrySize = 50; // Estimated size per aggregate entry
    const estimatedSizeBytes = baseSize + (this.aggregates.size * entrySize);
    
    return {
      aggregateCount: this.aggregates.size,
      estimatedSizeBytes
    };
  }

  /**
   * Clear all aggregates
   */
  clear(): void {
    this.aggregates.clear();
    this.stats.aggregateCount = 0;
  }

  // Private helper methods

  /**
   * Check if an event matches a target entity type
   * Uses pattern matching to identify entity-related events
   */
  private eventMatchesTarget(event: TemplateEvent, target: string): boolean {
    const template = event.template.toLowerCase();
    const targetLower = target.toLowerCase();
    
    // Universal target matches all events
    if (targetLower === "events") {
      return true;
    }
    
    // Direct match in template name
    if (template.includes(targetLower)) {
      return true;
    }
    
    // Standard CRUD patterns with singular/plural handling
    const singularTarget = this.getSingular(targetLower);
    const actions = ["create", "delete", "update", "add"];
    
    for (const action of actions) {
      if (template === `${action}_${singularTarget}` || 
          template === `${action}_${targetLower}`) {
        return true;
      }
    }
    
    // Entity-specific field matching (e.g., postId matches "posts")
    const entityIdField = `${singularTarget}Id`;
    if (event.params[entityIdField]) {
      return true;
    }
    
    return false;
  }

  /**
   * Convert plural to singular form (simple implementation)
   */
  private getSingular(word: string): string {
    return word.endsWith('s') ? word.slice(0, -1) : word;
  }

  /**
   * Update COUNT aggregate based on event type
   */
  private updateCount(entry: AggregateEntry, event: TemplateEvent): void {
    if (entry.value === null) {
      entry.value = 0;
    }
    
    const template = event.template.toUpperCase();
    
    if (template.startsWith("CREATE_")) {
      entry.value++;
    } else if (template.startsWith("DELETE_")) {
      entry.value = Math.max(0, entry.value - 1);
    }
  }

  /**
   * Update SUM aggregate by adding numeric field values
   */
  private updateSum(entry: AggregateEntry, event: TemplateEvent): void {
    const fieldValue = this.getNumericFieldValue(event, entry.definition.field);
    if (fieldValue === null) return;
    
    entry.value = (entry.value ?? 0) + fieldValue;
  }

  /**
   * Update AVG aggregate by tracking sum and count
   */
  private updateAvg(entry: AggregateEntry, event: TemplateEvent): void {
    const fieldValue = this.getNumericFieldValue(event, entry.definition.field);
    if (fieldValue === null || !entry.metadata) return;
    
    entry.metadata.sum = (entry.metadata.sum ?? 0) + fieldValue;
    entry.metadata.count = (entry.metadata.count ?? 0) + 1;
    
    entry.value = entry.metadata.sum / entry.metadata.count;
  }

  /**
   * Update MIN aggregate by tracking minimum value
   */
  private updateMin(entry: AggregateEntry, event: TemplateEvent): void {
    const fieldValue = this.getNumericFieldValue(event, entry.definition.field);
    if (fieldValue === null) return;
    
    if (entry.value === null || fieldValue < entry.value) {
      entry.value = fieldValue;
    }
  }

  /**
   * Update MAX aggregate by tracking maximum value
   */
  private updateMax(entry: AggregateEntry, event: TemplateEvent): void {
    const fieldValue = this.getNumericFieldValue(event, entry.definition.field);
    if (fieldValue === null) return;
    
    if (entry.value === null || fieldValue > entry.value) {
      entry.value = fieldValue;
    }
  }

  /**
   * Extract numeric field value from event parameters
   */
  private getNumericFieldValue(event: TemplateEvent, field?: string): number | null {
    if (!field) return null;
    
    const value = event.params[field];
    return typeof value === "number" ? value : null;
  }
}