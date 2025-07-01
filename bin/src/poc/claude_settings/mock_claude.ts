#!/usr/bin/env deno run --allow-all

/**
 * Mock Claude CLI for testing settings.json permission control
 * This simulates Claude Code's behavior for reading settings and applying permissions
 */

import { join } from "https://deno.land/std@0.224.0/path/mod.ts";

interface Settings {
  allowedTools?: string[];
  hooks?: {
    [eventName: string]: Array<{
      matcher: string;
      hooks: Array<{
        type: string;
        command: string;
      }>;
    }>;
  };
}

async function loadSettings(cwd: string): Promise<Settings> {
  try {
    const settingsPath = join(cwd, ".claude", "settings.json");
    const content = await Deno.readTextFile(settingsPath);
    return JSON.parse(content);
  } catch {
    return {};
  }
}

async function executeHook(event: string, settings: Settings, toolName?: string): Promise<boolean> {
  const eventHooks = settings.hooks?.[event] || [];
  
  for (const hookConfig of eventHooks) {
    if (toolName && hookConfig.matcher !== ".*" && !toolName.match(new RegExp(hookConfig.matcher))) {
      continue;
    }
    
    for (const hook of hookConfig.hooks) {
      if (hook.type === "command") {
        const cmd = new Deno.Command("sh", {
          args: ["-c", hook.command],
          stdout: "piped",
          stderr: "piped"
        });
        
        const process = cmd.spawn();
        const { code } = await process.output();
        
        if (code === 2) {
          return false; // Blocked
        }
      }
    }
  }
  
  return true;
}

async function main() {
  const args = Deno.args;
  const printIndex = args.indexOf("--print");
  if (printIndex === -1) {
    console.error("--print is required");
    Deno.exit(1);
  }
  
  const prompt = args.slice(printIndex + 1).join(" ");
  const cwd = Deno.cwd();
  
  // Load settings
  const settings = await loadSettings(cwd);
  
  // Simulate tool detection based on prompt
  let toolNeeded = "Read";
  if (prompt.includes("作成") || prompt.includes("create")) {
    toolNeeded = "Write";
  } else if (prompt.includes("echo") || prompt.includes("実行")) {
    toolNeeded = "Bash";
  }
  
  // Execute PreToolUse hooks
  const allowed = await executeHook("PreToolUse", settings, toolNeeded);
  if (!allowed) {
    console.error(`${toolNeeded} tool usage was blocked by hook`);
    Deno.exit(1);
  }
  
  // Check allowedTools
  if (settings.allowedTools && !settings.allowedTools.includes(toolNeeded)) {
    console.error(`${toolNeeded} tool is not allowed`);
    Deno.exit(1);
  }
  
  // Simulate tool execution
  console.log(`Executing ${toolNeeded} tool...`);
  
  if (toolNeeded === "Write") {
    await Deno.writeTextFile(join(cwd, "test.txt"), "Mock file created");
  }
  
  // Execute Stop hooks
  await executeHook("Stop", settings);
  
  console.log("Done");
  Deno.exit(0);
}

if (import.meta.main) {
  main();
}