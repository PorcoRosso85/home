#!/bin/bash
# Demo script for Claude session continuity

echo "=== Claude Session Continuity Demo ==="
echo
echo "1. Python implementation:"
echo "   Run: python claude_continue.py"
echo "   Test: uv run pytest session.py -v"
echo
echo "2. TypeScript implementation:"
echo "   Run: npm run claude"
echo "   Test: npm test"
echo
echo "Both implementations provide:"
echo "- Session history management"
echo "- Context building for --continue"
echo "- Stream JSON parsing"
echo "- Immutable state management"
echo
echo "Example session flow:"
echo "> say bye"
echo "[Claude responds: bye]"
echo "> what did you say"
echo "[Claude responds: I said 'bye']"
echo "> exit"