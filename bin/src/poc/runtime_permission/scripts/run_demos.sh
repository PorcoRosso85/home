#!/usr/bin/env bash

echo "🦕 Deno Runtime Permission Demos"
echo "================================"
echo ""

echo "1️⃣  Running file access demo WITHOUT permissions:"
echo "   $ deno run src/file_access.ts"
deno run src/file_access.ts 2>&1 | head -20
echo ""

echo "2️⃣  Running file access demo WITH read permission for ./src:"
echo "   $ deno run --allow-read=./src src/file_access.ts"
deno run --allow-read=./src src/file_access.ts 2>&1 | head -20
echo ""

echo "3️⃣  Running network access demo WITHOUT permissions:"
echo "   $ deno run src/network_access.ts"
deno run src/network_access.ts 2>&1 | head -15
echo ""

echo "4️⃣  Running network access demo WITH permission for api.github.com:"
echo "   $ deno run --allow-net=api.github.com src/network_access.ts"
deno run --allow-net=api.github.com src/network_access.ts 2>&1 | head -15
echo ""

echo "5️⃣  Running environment variable demo WITHOUT permissions:"
echo "   $ deno run src/env_access.ts"
deno run src/env_access.ts 2>&1 | head -20
echo ""

echo "6️⃣  Running subprocess demo WITHOUT permissions:"
echo "   $ deno run src/subprocess.ts"
deno run src/subprocess.ts 2>&1 | head -15
echo ""

echo "7️⃣  Running all tests:"
echo "   $ deno test --allow-read=./src --allow-net=api.github.com --allow-env=HOME,USER --allow-run=echo"
deno test --allow-read=./src --allow-net=api.github.com --allow-env=HOME,USER --allow-run=echo
echo ""

echo "✨ Demo complete!"
echo "   Notice how Deno's permission system provides fine-grained control"
echo "   over what the code can access, all from simple command-line flags."