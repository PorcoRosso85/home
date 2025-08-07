// CLI entry point - JSON I/O
import { processRequest } from "./mod";

async function main() {
  try {
    // Read JSON from stdin
    const input = await Bun.stdin.text();
    
    if (!input.trim()) {
      console.error(JSON.stringify({
        ok: false,
        error: "No input provided"
      }));
      process.exit(1);
    }
    
    const request = JSON.parse(input);
    const result = processRequest(request);
    
    // Output JSON to stdout
    if (result.ok) {
      console.log(JSON.stringify(result.data));
    } else {
      console.error(JSON.stringify({
        error: result.error.message || "Unknown error"
      }));
      process.exit(1);
    }
  } catch (error) {
    console.error(JSON.stringify({
      ok: false,
      error: error instanceof Error ? error.message : "Unknown error"
    }));
    process.exit(1);
  }
}

main();