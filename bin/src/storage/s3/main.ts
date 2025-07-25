#!/usr/bin/env -S deno run --allow-all

/**
 * S3 Storage CLI - LLM-first interface
 * 
 * This CLI provides an interactive, JSON-based interface for S3 operations.
 * It's designed to be easily used by LLMs and humans alike.
 * 
 * Usage:
 *   # Interactive mode
 *   deno run --allow-all main.ts
 *   
 *   # Direct command mode
 *   deno run --allow-all main.ts '{"action": "list", "prefix": "photos/"}'
 *   
 *   # Pipe JSON input
 *   echo '{"action": "list"}' | deno run --allow-all main.ts
 * 
 * Environment variables:
 *   S3_REGION - AWS region (required)
 *   S3_ACCESS_KEY_ID - AWS access key (required)
 *   S3_SECRET_ACCESS_KEY - AWS secret key (required)
 *   S3_BUCKET - Default bucket name (required)
 *   S3_ENDPOINT - Custom endpoint for S3-compatible services (optional)
 */

import { executeS3Command } from './mod.ts';
import type { S3Command, S3Config } from './domain.ts';
import { getS3Config, validateS3Environment } from './variables.ts';

async function main() {
  try {
    // Validate environment variables
    validateS3Environment();
    const envConfig = getS3Config();
    
    // Convert environment config to S3Config
    const config: S3Config = {
      endpoint: envConfig.S3_ENDPOINT,
      region: envConfig.S3_REGION,
      accessKeyId: envConfig.S3_ACCESS_KEY_ID,
      secretAccessKey: envConfig.S3_SECRET_ACCESS_KEY,
      bucket: envConfig.S3_BUCKET,
    };

    // Check if we have command line arguments
    const args = Deno.args;
    
    if (args.length > 0) {
      // Direct command mode
      const commandJson = args[0];
      await executeCommand(commandJson, config);
    } else {
      // Check if we have piped input
      const isInteractive = Deno.stdin.isTerminal();
      
      if (!isInteractive) {
        // Read from pipe
        const decoder = new TextDecoder();
        const input = await Deno.stdin.readable.getReader().read();
        if (input.value) {
          const commandJson = decoder.decode(input.value).trim();
          await executeCommand(commandJson, config);
        }
      } else {
        // Interactive mode
        await runInteractiveMode(config);
      }
    }
  } catch (error) {
    console.error(JSON.stringify({
      type: 'error',
      message: error instanceof Error ? error.message : 'Unknown error',
      details: error,
    }));
    Deno.exit(1);
  }
}

async function executeCommand(commandJson: string, config: S3Config) {
  try {
    const command = JSON.parse(commandJson) as S3Command;
    const result = await executeS3Command(command, config);
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    if (error instanceof SyntaxError) {
      console.error(JSON.stringify({
        type: 'error',
        message: 'Invalid JSON input',
        details: error.message,
      }));
    } else {
      throw error;
    }
  }
}

async function runInteractiveMode(config: S3Config) {
  console.log('S3 Storage CLI - Interactive Mode');
  console.log('================================');
  console.log('');
  console.log('Enter JSON commands or type "help" for examples.');
  console.log('Type "exit" or press Ctrl+C to quit.');
  console.log('');

  // Show help on start
  const helpResult = await executeS3Command({ action: 'help' }, config);
  console.log(JSON.stringify(helpResult, null, 2));
  console.log('');

  const decoder = new TextDecoder();
  const encoder = new TextEncoder();
  
  while (true) {
    // Prompt
    await Deno.stdout.write(encoder.encode('\n> '));
    
    // Read input
    const buf = new Uint8Array(1024);
    const n = await Deno.stdin.read(buf);
    
    if (n === null) {
      // EOF
      break;
    }
    
    const input = decoder.decode(buf.subarray(0, n)).trim();
    
    if (input === 'exit') {
      console.log('Goodbye!');
      break;
    }
    
    if (input === 'help') {
      const helpResult = await executeS3Command({ action: 'help' }, config);
      console.log(JSON.stringify(helpResult, null, 2));
      continue;
    }
    
    if (input === '') {
      continue;
    }
    
    // Execute command
    await executeCommand(input, config);
  }
}

// Run main function
if (import.meta.main) {
  main();
}