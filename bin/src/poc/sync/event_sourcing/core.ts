/**
 * Event Sourcing Core Logic
 * イベントソーシングのコアロジック（純粋関数）
 */

import type { TemplateEvent, TemplateMetadata, Impact, Conflict } from "./types.ts";

// ========== Event Generation ==========

export const generateEventId = (): string => {
  return `evt_${crypto.randomUUID()}`;
};

export const createTemplateEvent = (
  template: string,
  params: Record<string, any>,
  clientId: string
): TemplateEvent => {
  const event: TemplateEvent = {
    id: generateEventId(),
    template,
    params: { ...params },
    timestamp: Date.now(),
    clientId,
    checksum: calculateChecksum(template, params)
  };
  
  return event;
};

export const calculateChecksum = (template: string, params: Record<string, any>): string => {
  const content = JSON.stringify({ template, params });
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    const char = content.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(16).padEnd(64, '0');
};

// ========== Validation ==========

export const validateParams = (
  params: Record<string, any>,
  metadata: TemplateMetadata
): Record<string, any> => {
  // Check required params
  for (const required of metadata.requiredParams) {
    if (!(required in params)) {
      throw new Error(`Missing required parameter: ${required}`);
    }
  }

  // Check types if specified
  if (metadata.paramTypes) {
    for (const [param, expectedType] of Object.entries(metadata.paramTypes)) {
      if (param in params) {
        const actualType = typeof params[param];
        if (actualType !== expectedType && expectedType === "number" && actualType === "string") {
          const parsed = Number(params[param]);
          if (isNaN(parsed)) {
            throw new Error(`Invalid type for parameter ${param}: expected ${expectedType}, got ${actualType}`);
          }
        }
      }
    }
  }

  // Sanitize values
  const sanitized: Record<string, any> = {};
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === "string") {
      // Remove SQL injection attempts
      sanitized[key] = value
        .replace(/;/g, "")
        .replace(/--/g, "")
        .replace(/DROP/gi, "")
        .replace(/DELETE/gi, "")
        .replace(/UPDATE/gi, "")
        .replace(/INSERT/gi, "");
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
};

// ========== Impact Prediction ==========

export const predictImpact = (
  templateName: string,
  metadata: TemplateMetadata
): Impact => {
  const impact: Impact = {
    addedNodes: 0,
    addedEdges: 0,
    deletedNodes: 0
  };

  switch (metadata.impact) {
    case "CREATE_NODE":
      impact.addedNodes = 1;
      break;
    case "CREATE_EDGE":
      impact.addedEdges = 1;
      if (templateName === "FOLLOW_USER") {
        impact.edgeType = "FOLLOWS";
      }
      break;
    case "DELETE_NODE":
      impact.deletedNodes = 1;
      impact.warning = "Actual count may vary (estimated)";
      break;
  }

  return impact;
};

// ========== Conflict Detection ==========

export const detectConflicts = (events: TemplateEvent[]): Conflict[] => {
  const conflicts: Conflict[] = [];
  const eventsByTarget = new Map<string, TemplateEvent[]>();
  
  // Group events by target
  for (const event of events) {
    const targetId = event.params.id || `${event.params.followerId}-${event.params.targetId}`;
    if (targetId) {
      const existing = eventsByTarget.get(targetId) || [];
      existing.push(event);
      eventsByTarget.set(targetId, existing);
    }
  }
  
  // Find conflicts
  for (const [targetId, targetEvents] of eventsByTarget) {
    if (targetEvents.length > 1) {
      // Check if events are concurrent (within 100ms)
      const sorted = targetEvents.sort((a, b) => a.timestamp - b.timestamp);
      for (let i = 0; i < sorted.length - 1; i++) {
        if (sorted[i + 1].timestamp - sorted[i].timestamp < 100) {
          conflicts.push({
            type: "CONCURRENT_UPDATE",
            events: [sorted[i], sorted[i + 1]]
          });
        }
      }
    }
  }
  
  return conflicts;
};

// ========== Event Filtering ==========

export const filterEventsSince = (
  events: TemplateEvent[],
  timestamp: number,
  excludeClientId?: string
): TemplateEvent[] => {
  return events.filter(e => 
    e.timestamp > timestamp && 
    (!excludeClientId || e.clientId !== excludeClientId)
  );
};

export const getLatestEvents = (
  events: TemplateEvent[],
  count: number
): TemplateEvent[] => {
  const start = Math.max(0, events.length - count);
  return events.slice(start);
};

// ========== Checksum Validation ==========

export const validateChecksum = (event: TemplateEvent): boolean => {
  if (!event.checksum) {
    return false;
  }
  
  const calculated = calculateChecksum(event.template, event.params);
  return calculated === event.checksum;
};