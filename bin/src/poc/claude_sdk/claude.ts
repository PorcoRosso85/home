#!/usr/bin/env tsx
import { spawn } from "child_process"
import { readFile, writeFile, mkdir, appendFile } from "fs/promises"
import { join } from "path"

// Parse arguments
export function parseArgs(args: string[]) {
  const uriIndex = args.indexOf("--uri")
  const printIndex = args.indexOf("--print")
  
  if (uriIndex === -1 || printIndex === -1) {
    throw new Error("Usage: tsx claude.ts --uri <directory> --print <prompt>")
  }
  
  const uri = args[uriIndex + 1]
  const prompt = args.slice(printIndex + 1).join(" ")
  
  if (!uri || !prompt) {
    throw new Error("Both --uri and --print are required")
  }
  
  return { uri, prompt }
}

// Persistence layer
export async function loadSession(dir: string) {
  try {
    return JSON.parse(await readFile(join(dir, "session.json"), "utf8"))
  } catch {
    return { h: [] }
  }
}

export async function saveSession(dir: string, session: any) {
  await mkdir(dir, { recursive: true })
  await writeFile(join(dir, "session.json"), JSON.stringify(session, null, 2))
}

export async function appendStream(dir: string, line: string) {
  await appendFile(join(dir, "stream.jsonl"), line + "\n")
}

export function buildPrompt(history: Array<[string, string]>, prompt: string): string {
  if (history.length === 0) return prompt
  const context = history.slice(-6).map(([r, c]) => `${r}: ${c}`).join("\n")
  return `${context}\n\nUser: ${prompt}`
}

// Main function
export async function main(args: string[]) {
  const { uri, prompt } = parseArgs(args)
  
  // Load session
  const session = await loadSession(uri)
  
  // Build prompt with context
  const fullPrompt = buildPrompt(session.h, prompt)
  
  // Run claude
  const cmd = ["--output-format", "stream-json", "--verbose", "--print", fullPrompt]
  if (session.h.length) cmd.push("--continue")
  
  const proc = spawn("claude", cmd, { 
    stdio: ["pipe", "pipe", "pipe"],
    env: { ...process.env, CLAUDE_NON_INTERACTIVE: "1" },
    cwd: uri  // Set working directory to --uri path
  })
  
  // Close stdin to signal we're not sending more input
  proc.stdin.end()
  let response = ""
  
  // Ensure directory exists for stream
  await mkdir(uri, { recursive: true })
  
  // Handle spawn errors
  proc.on("error", (err) => {
    console.error("Failed to spawn claude:", err)
    console.error("Make sure 'claude' CLI is installed and in PATH")
    process.exit(1)
  })
  
  // Process stream
  let buffer = ""
  proc.stdout.on("data", chunk => {
    buffer += chunk.toString()
    const lines = buffer.split("\n")
    buffer = lines.pop() || "" // Keep incomplete line in buffer
    
    for (const line of lines.filter(Boolean)) {
      console.log(line)
      // Save stream line
      appendStream(uri, line).catch(console.error)
      
      try {
        const json = JSON.parse(line)
        if (json.type === "assistant" && json.message?.content?.[0]?.text) {
          response += json.message.content[0].text
        }
      } catch {}
    }
  })
  
  // Process any remaining buffer on close
  proc.stdout.on("end", () => {
    if (buffer.trim()) {
      console.log(buffer)
      appendStream(uri, buffer).catch(console.error)
    }
  })
  
  proc.stderr.on("data", chunk => {
    process.stderr.write(chunk)
  })
  
  await new Promise<number>(r => proc.on("exit", r))
  
  // Save session
  if (response) {
    session.h.push(["user", prompt], ["assistant", response])
    await saveSession(uri, session)
  }
}

// In-source tests only when NODE_TEST is set
if (process.env.NODE_TEST === "1") {
  (async () => {
    const { test } = await import("node:test")
    const assert = await import("node:assert/strict")
  
  test("parseArgs_valid_returnsUriAndPrompt", () => {
    const result = parseArgs(["--uri", "test", "--print", "hello", "world"])
    assert.equal(result.uri, "test")
    assert.equal(result.prompt, "hello world")
  })

  test("parseArgs_missingUri_throwsError", () => {
    assert.throws(
      () => parseArgs(["--print", "test"]),
      /Usage:/
    )
  })

  test("parseArgs_missingPrint_throwsError", () => {
    assert.throws(
      () => parseArgs(["--uri", "test"]),
      /Usage:/
    )
  })

  test("parseArgs_emptyValues_throwsError", () => {
    assert.throws(
      () => parseArgs(["--uri", "", "--print", ""]),
      /required/
    )
  })

  test("buildPrompt_noHistory_returnsPrompt", () => {
    const result = buildPrompt([], "hello")
    assert.equal(result, "hello")
  })

  test("buildPrompt_withHistory_includesContext", () => {
    const history: Array<[string, string]> = [
      ["user", "hi"],
      ["assistant", "hello"]
    ]
    const result = buildPrompt(history, "bye")
    assert.ok(result.includes("user: hi"))
    assert.ok(result.includes("assistant: hello"))
    assert.ok(result.includes("User: bye"))
  })

  test("buildPrompt_longHistory_limitsToSix", () => {
    const history: Array<[string, string]> = Array.from(
      { length: 10 },
      (_, i) => ["user", `msg${i}`]
    )
    const result = buildPrompt(history, "new")
    assert.ok(result.includes("msg9"))
    assert.ok(!result.includes("msg3"))
  })
  })()
}

// Execute main if run directly and not in test mode
if (import.meta.url === `file://${process.argv[1]}` && process.env.NODE_TEST !== "1") {
  main(process.argv.slice(2)).catch((err) => {
    console.error(err.message)
    process.exit(1)
  })
}