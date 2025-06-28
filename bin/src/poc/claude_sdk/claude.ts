#!/usr/bin/env deno run --allow-all

import { parseArgs, loadSession, saveSession, appendStream, buildPrompt } from "./core.ts";

// Main function
export async function main(args: string[]): Promise<void> {
  const { uri, prompt } = parseArgs(args);
  
  // Load session
  const session = await loadSession(uri);
  
  // Build prompt with context
  const fullPrompt = buildPrompt(session.h, prompt);
  
  // Run claude
  const cmd = ["claude", "--output-format", "stream-json", "--verbose", "--print", fullPrompt];
  if (session.h.length) cmd.push("--continue");
  
  const command = new Deno.Command(cmd[0], {
    args: cmd.slice(1),
    cwd: uri,
    env: { ...Deno.env.toObject(), CLAUDE_NON_INTERACTIVE: "1" },
    stdin: "null",
    stdout: "piped",
    stderr: "piped",
  });
  
  // Ensure directory exists for stream
  await Deno.mkdir(uri, { recursive: true });
  
  const process = command.spawn();
  let response = "";
  
  // Process stdout
  const decoder = new TextDecoder();
  const reader = process.stdout.getReader();
  let buffer = "";
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      
      for (const line of lines.filter(Boolean)) {
        console.log(line);
        try {
          await appendStream(uri, line);
        } catch (error) {
          console.error("Failed to append stream:", error);
        }
        
        try {
          const json = JSON.parse(line);
          if (json.type === "assistant" && json.message?.content?.[0]?.text) {
            response += json.message.content[0].text;
          }
        } catch {
          // Ignore JSON parse errors
        }
      }
    }
    
    // Process remaining buffer
    if (buffer.trim()) {
      console.log(buffer);
      try {
        await appendStream(uri, buffer);
      } catch (error) {
        console.error("Failed to append stream:", error);
      }
    }
  } finally {
    reader.releaseLock();
  }
  
  // Process stderr
  const stderrReader = process.stderr.getReader();
  try {
    while (true) {
      const { done, value } = await stderrReader.read();
      if (done) break;
      await Deno.stderr.write(value);
    }
  } finally {
    stderrReader.releaseLock();
  }
  
  const { code } = await process.status;
  if (code !== 0) {
    throw new Error(`Claude exited with code ${code}`);
  }
  
  // Save session
  if (response) {
    session.h.push(["user", prompt], ["assistant", response]);
    await saveSession(uri, session);
  }
}

// Execute main if run directly
if (import.meta.main) {
  main(Deno.args).catch((err) => {
    console.error(err.message);
    Deno.exit(1);
  });
}