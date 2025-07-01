import { join, dirname, fromFileUrl } from "https://deno.land/std@0.224.0/path/mod.ts";

/**
 * Get the appropriate Claude command - use poc/claude_sdk
 */
export async function getClaudeCommand(): Promise<string[]> {
  // Use poc/claude_sdk as a wrapper - resolve relative to this file
  const thisDir = dirname(fromFileUrl(import.meta.url));
  const sdkPath = join(thisDir, "../claude_sdk/claude.ts");
  return ["deno", "run", "--allow-all", sdkPath];
}

/**
 * Create a mock settings.json file in the test directory
 */
export async function createSettings(dir: string, settings: unknown): Promise<void> {
  const settingsDir = join(dir, ".claude");
  await Deno.mkdir(settingsDir, { recursive: true });
  await Deno.writeTextFile(
    join(settingsDir, "settings.json"),
    JSON.stringify(settings, null, 2)
  );
}