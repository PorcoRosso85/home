#!/usr/bin/env deno run

console.log("🚀 Subprocess Execution Demo");
console.log("===========================");

async function tryRunCommand(cmd: string[], description: string) {
  try {
    const command = new Deno.Command(cmd[0], {
      args: cmd.slice(1),
    });
    
    const { code, stdout, stderr } = await command.output();
    
    console.log(`✅ Successfully executed ${description}:`);
    console.log(`   Exit code: ${code}`);
    if (stdout.length > 0) {
      const output = new TextDecoder().decode(stdout);
      console.log(`   Output: ${output.trim().substring(0, 100)}${output.length > 100 ? '...' : ''}`);
    }
  } catch (error) {
    console.log(`❌ Failed to execute ${description}:`);
    console.log(`   Error: ${error.message}`);
  }
}

console.log("\n1. Attempting to run 'echo Hello World':");
await tryRunCommand(["echo", "Hello", "World"], "echo");

console.log("\n2. Attempting to run 'ls -la':");
await tryRunCommand(["ls", "-la"], "ls");

console.log("\n3. Attempting to run 'curl --version':");
await tryRunCommand(["curl", "--version"], "curl");

console.log("\n4. Attempting to run 'cat /etc/passwd':");
await tryRunCommand(["cat", "/etc/passwd"], "cat /etc/passwd");

console.log("\n");
console.log("💡 Try running with different permissions:");
console.log("   deno run --allow-run=echo src/subprocess.ts");
console.log("   deno run --allow-run=echo,ls src/subprocess.ts");
console.log("   deno run --allow-run src/subprocess.ts");