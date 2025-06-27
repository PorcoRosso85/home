#!/usr/bin/env tsx
/**
 * Claude CLI with session continuity
 * Follows bin/docs/CONVENTION.yaml
 */
import { spawn } from "child_process";
import { createInterface } from "readline";
import {
  parseJson,
  addToHistory,
  buildContext,
  extractAssistantText,
  type SessionHistory,
} from "./sessionManager";

/**
 * Create Claude subprocess with proper arguments
 */
function runClaudeCommand(prompt: string, continueSession = false) {
  const args = [
    "--output-format", "stream-json",
    "--verbose",
    "--print", prompt,
  ];
  
  if (continueSession) {
    args.push("--continue");
  }
  
  return spawn("claude", args, { stdio: ["inherit", "pipe", "pipe"] });
}

/**
 * Process streaming output and update history
 */
async function processStream(
  process: ReturnType<typeof spawn>,
  history: SessionHistory
): Promise<SessionHistory> {
  let updatedHistory = history;
  
  for await (const chunk of process.stdout) {
    const lines = chunk.toString().split("\n").filter(Boolean);
    
    for (const line of lines) {
      console.log(line); // Echo the stream
      
      const result = parseJson(line);
      if (result.ok && result.data.type === "assistant") {
        const text = extractAssistantText(result.data);
        if (text) {
          updatedHistory = addToHistory(updatedHistory, "assistant", text);
        }
      }
    }
  }
  
  return updatedHistory;
}

/**
 * Create interactive session loop
 */
async function createSessionLoop() {
  let history: SessionHistory = [];
  
  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: "> ",
  });
  
  console.log("Claude session (type 'exit' to quit)");
  
  rl.prompt();
  
  for await (const userInput of rl) {
    if (userInput.toLowerCase() === "exit") {
      rl.close();
      break;
    }
    
    // Build prompt with context
    let fullPrompt = userInput;
    if (history.length > 0) {
      const context = buildContext(history);
      fullPrompt = `${context}\n\nUser: ${userInput}`;
    }
    
    // Run command
    const proc = runClaudeCommand(fullPrompt, history.length > 0);
    
    // Update history with user input
    history = addToHistory(history, "user", userInput);
    
    // Process response
    history = await processStream(proc, history);
    
    // Wait for completion
    await new Promise((resolve) => proc.on("close", resolve));
    
    rl.prompt();
  }
}

// Main execution
if (import.meta.url === `file://${process.argv[1]}`) {
  createSessionLoop().catch(console.error);
}