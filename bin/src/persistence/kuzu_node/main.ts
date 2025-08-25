#!/usr/bin/env node
/**
 * CLI entry point
 */

import { runInMemoryExample } from './application';

async function main() {
  console.log('🚀 KuzuDB Example');
  
  try {
    const results = await runInMemoryExample();
    console.log('Results:', results);
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

if (import.meta.main) {
  main();
}