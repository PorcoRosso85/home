#!/usr/bin/env node
/**
 * Switchover script for safe production migration
 * 
 * This script allows switching between legacy (scrape.mjs) and 
 * TypeScript (src/main.ts) implementations based on environment variables.
 * 
 * Usage:
 *   npm run scrape                 # Uses TypeScript implementation (default)
 *   USE_LEGACY=true npm run scrape # Uses legacy implementation
 */

import { spawn } from 'child_process'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const projectRoot = join(__dirname, '..')

function main() {
  const useLegacy = process.env.USE_LEGACY === 'true'
  
  console.log('🔄 Corporate List Scraper Switchover')
  console.log(`   Implementation: ${useLegacy ? 'Legacy (scrape.mjs)' : 'TypeScript (src/main.ts)'}`)
  console.log(`   Environment: USE_LEGACY=${process.env.USE_LEGACY || 'undefined'}`)
  console.log('==================================================')

  let command, args, scriptPath

  if (useLegacy) {
    // Use legacy implementation
    command = 'node'
    scriptPath = join(projectRoot, 'scrape.mjs')
    args = [scriptPath, ...process.argv.slice(2)]
    console.log(`🔧 Running: ${command} ${args.join(' ')}`)
  } else {
    // Use TypeScript implementation (default)
    command = 'npx'
    scriptPath = 'tsx'
    args = [scriptPath, join(projectRoot, 'src/main.ts'), ...process.argv.slice(2)]
    console.log(`🔧 Running: ${command} ${args.join(' ')}`)
  }

  // Spawn the appropriate process
  const child = spawn(command, args, {
    stdio: 'inherit',
    cwd: projectRoot,
    env: {
      ...process.env,
      // Ensure all environment variables are passed through
      IMPLEMENTATION_TYPE: useLegacy ? 'legacy' : 'typescript'
    }
  })

  // Handle child process exit
  child.on('close', (code) => {
    console.log(`\n🏁 Process exited with code ${code}`)
    process.exit(code)
  })

  // Handle errors
  child.on('error', (error) => {
    console.error(`💥 Failed to start process: ${error.message}`)
    process.exit(1)
  })

  // Handle interrupt signals
  process.on('SIGINT', () => {
    console.log('\n⏹️  Received SIGINT, stopping...')
    child.kill('SIGINT')
  })

  process.on('SIGTERM', () => {
    console.log('\n⏹️  Received SIGTERM, stopping...')
    child.kill('SIGTERM')
  })
}

main()