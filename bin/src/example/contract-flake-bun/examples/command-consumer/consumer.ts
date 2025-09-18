import { spawn } from 'child_process';

const execCommand = async (command: string[], input?: string): Promise<string> => {
  return new Promise((resolve, reject) => {
    const proc = spawn(command[0], command.slice(1));
    const chunks: Buffer[] = [];
    const errorChunks: Buffer[] = [];
    
    proc.stdout.on('data', (data) => chunks.push(data));
    proc.stderr.on('data', (data) => errorChunks.push(data));
    
    if (input) {
      proc.stdin.write(input);
      proc.stdin.end();
    }
    
    proc.on('close', (code) => {
      const output = Buffer.concat(chunks).toString();
      const error = Buffer.concat(errorChunks).toString();
      if (code === 0) resolve(output);
      else reject(new Error(error || `Exit code: ${code}`));
    });
  });
};

async function main() {
  const testData = {
    items: [
      { id: 1, name: "Item 1" },
      { id: 2, name: "Item 2" },
      { id: 3, name: "Item 3" }
    ]
  };
  
  try {
    // Level 3: No path needed, just command name!
    const result = await execCommand(
      ['data-processor', '--process'],
      JSON.stringify(testData)
    );
    
    const parsed = JSON.parse(result);
    console.log("Processing Report:");
    console.log("==================");
    console.log(`Items processed: ${parsed.processed}`);
    console.log(`Items failed: ${parsed.failed}`);
    console.log("Output:", JSON.stringify(parsed.output, null, 2));
  } catch (error) {
    console.error("Error:", error);
    process.exit(1);
  }
}

main();