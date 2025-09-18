/**
 * Archive Policy
 * Determines if events should be archived based on age
 */

import type { TemplateEvent } from "../types.ts";

/**
 * Determines if an event should be archived based on its age
 * @param event - The event to check
 * @param currentTime - The current time in milliseconds
 * @returns true if the event is 30 or more days old, false otherwise
 */
export function shouldArchive(event: TemplateEvent, currentTime: number): boolean {
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  const thirtyDaysInMs = 30 * millisecondsPerDay;
  
  const eventAge = currentTime - event.timestamp;
  
  return eventAge >= thirtyDaysInMs;
}