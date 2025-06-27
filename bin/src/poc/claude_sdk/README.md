# Claude Continue

Minimal Claude CLI wrapper with automatic session continuation.

## Usage

```bash
# Both --uri and --print are required
tsx claude.ts --uri <directory> --print <prompt>

# Examples
tsx claude.ts --uri .claude --print "say hello"
tsx claude.ts --uri /tmp/session --print "what's 2+2?"

# Via npm
npm run claude -- --uri .claude --print "your prompt"
```

## Features

- Always uses `--output-format stream-json --verbose`
- Automatically adds `--continue` when session exists
- Saves conversation history to `<uri>/session.json`
- Saves stream output to `<uri>/stream.jsonl` (append mode)
- Maintains last 6 exchanges as context
- **Sets Claude Code's working directory (cwd) to the `--uri` path**
- **Each directory maintains its own independent session**

## Arguments

- `--uri <directory>` - Required. Directory for session storage AND Claude's working directory
- `--print <prompt>` - Required. Your prompt to Claude

## Files Created

- `<uri>/session.json` - Conversation history
- `<uri>/stream.jsonl` - Raw JSON stream (one JSON per line)

## Implementation

Single file: `claude.ts` (191 lines)