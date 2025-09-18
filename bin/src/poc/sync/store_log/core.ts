// 純粋なビジネスロジック

import type { CausalOperation } from "./types.ts";

export function createEventLine(event: CausalOperation): string {
  return JSON.stringify(event) + '\n';
}

export function parseEventLine(line: string): CausalOperation | null {
  if (!line.trim()) {
    return null;
  }
  
  try {
    return JSON.parse(line) as CausalOperation;
  } catch {
    return null;
  }
}

export function parseEventLines(content: string): CausalOperation[] {
  return content
    .trim()
    .split('\n')
    .map(parseEventLine)
    .filter((event): event is CausalOperation => event !== null);
}

export function calculateOffset(lines: string[]): number {
  const validLines = lines.filter(line => line.trim().length > 0);
  return validLines.length > 0 ? validLines.length - 1 : -1;
}