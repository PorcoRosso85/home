# Claude SDK for Deno

Minimal Claude CLI wrapper with automatic session continuation, built for Deno.

## Usage

```bash
# Run with deno task
deno task claude --uri <directory> --print <prompt>

# Examples
deno task claude --uri .claude --print "say hello"
deno task claude --uri /tmp/session --print "what's 2+2?"

# Run directly
deno run --allow-all claude.ts --uri .claude --print "your prompt"
```

## Features

- Always uses `--output-format stream-json --verbose`
- Automatically adds `--continue` when session exists
- Saves conversation history to `<uri>/session.json`
- Saves stream output with metadata to `<uri>/stream.jsonl`
- Maintains last 6 exchanges as context
- **Sets Claude Code's working directory (cwd) to the `--uri` path**
- **Each directory maintains its own independent session**
- Standard error handling with try/catch
- Full Deno compatibility

## Arguments

- `--uri <directory>` - Required. Directory for session storage AND Claude's working directory
- `--print <prompt>` - Required. Your prompt to Claude

## Files Created

- `<uri>/session.json` - Conversation history
- `<uri>/stream.jsonl` - JSON stream with metadata (id, timestamp, data)

## Development

```bash
# Run tests
deno task test

# Format code
deno task fmt

# Lint code
deno task lint

# Run all checks
deno task check
```

## Module Structure

- `claude.ts` - Main executable
- `core.ts` - Core business logic
- `types.ts` - Type definitions
- `mod.ts` - Module exports
- `claude.test.ts` - Tests