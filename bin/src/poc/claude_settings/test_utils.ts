import { join } from "https://deno.land/std@0.224.0/path/mod.ts";

/**
 * Get the appropriate Claude command based on availability
 */
export async function getClaudeCommand(): Promise<string[]> {
  // Check if real Claude CLI is available
  try {
    const cmd = new Deno.Command("which", {
      args: ["claude"],
      stdout: "piped",
      stderr: "piped"
    });
    
    const { code } = await cmd.output();
    if (code === 0) {
      return ["claude"];
    }
  } catch {
    // Continue to mock
  }
  
  // Use mock Claude
  const mockPath = join(Deno.cwd(), "mock_claude.ts");
  return ["deno", "run", "--allow-all", mockPath];
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