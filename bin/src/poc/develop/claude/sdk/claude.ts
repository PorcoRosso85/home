#!/usr/bin/env deno run --allow-all

import { parseArgs, loadSession, saveSession, appendStream, buildPrompt, formatToJsonl, formatToJsonlWithWorktree } from "./core.ts";

// Main function
export async function main(args: string[]): Promise<void> {
  const { claudeId, uri, prompt, allowWrite } = parseArgs(args);
  
  // Load session
  const session = await loadSession(uri);
  
  // Build prompt with context
  const fullPrompt = buildPrompt(session.h, prompt);
  
  // Run claude
  const cmd = ["claude", "--output-format", "stream-json", "--verbose"];
  
  // Add permission inheritance options if requested
  if (allowWrite) {
    cmd.push("--add-dir", uri);
    cmd.push("--allowedTools", "Write,Edit,MultiEdit,Bash,Read,Glob,Grep,LS");
  }
  
  cmd.push("--print", fullPrompt);
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
  
  // Log user input to stream
  const userEntry = {
    type: "user",
    prompt: prompt,
    fullPrompt: fullPrompt,
    timestamp: new Date().toISOString()
  };
  const userJsonl = formatToJsonlWithWorktree(userEntry, uri);
  console.log(userJsonl);
  await appendStream(uri, userJsonl);
  
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
        try {
          const json = JSON.parse(line);
          const jsonl = formatToJsonlWithWorktree(json, uri);
          console.log(jsonl);
          await appendStream(uri, jsonl);
          
          if (json.type === "assistant" && json.message?.content?.[0]?.text) {
            response += json.message.content[0].text;
          }
        } catch (error) {
          // For non-JSON lines, output as-is
          console.log(line);
          await appendStream(uri, line);
        }
      }
    }
    
    // Process remaining buffer
    if (buffer.trim()) {
      try {
        const json = JSON.parse(buffer);
        const jsonl = formatToJsonlWithWorktree(json, uri);
        console.log(jsonl);
        await appendStream(uri, jsonl);
      } catch {
        console.log(buffer);
        await appendStream(uri, buffer);
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