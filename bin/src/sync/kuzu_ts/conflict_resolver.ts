/**
 * Conflict Resolver Implementation
 * 競合解決実装
 */

import type { ConflictResolver, ConflictResolution } from "./types.ts";
import type { TemplateEvent } from "./event_sourcing/types.ts";

export class ConflictResolverImpl implements ConflictResolver {
  resolve(events: TemplateEvent[]): ConflictResolution {
    if (events.length === 0) {
      throw new Error("No events to resolve");
    }
    
    if (events.length === 1) {
      return {
        strategy: "NO_CONFLICT",
        winner: events[0],
        conflicts: []
      };
    }
    
    // Sort by timestamp (Last Write Wins)
    const sorted = [...events].sort((a, b) => 
      (b.timestamp || 0) - (a.timestamp || 0)
    );
    
    return {
      strategy: "LAST_WRITE_WINS",
      winner: sorted[0],
      conflicts: sorted.slice(1)
    };
  }
}