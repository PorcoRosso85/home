#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * Remote State Fetcher for Cloudflare Resources
 *
 * Fetches current state from Cloudflare using wrangler CLI commands and normalizes
 * the output to a format compatible with SOT comparison. Follows YAGNI principle
 * by using wrangler CLI instead of direct API calls.
 *
 * Usage:
 *   fetch-remote-state --env dev
 *   fetch-remote-state --env prod --output ./state/
 *   fetch-remote-state --env stg --format json --verbose
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration constants
const CONFIG = {
  supportedEnvironments: ['dev', 'stg', 'prod'],
  defaultOutputDir: './generated',
  outputFilename: 'remote-state.json',
  wranglerCommands: {
    whoami: 'wrangler whoami',
    listR2Buckets: 'wrangler r2 bucket list',
    listWorkers: 'wrangler deployments list',
    listSecrets: 'wrangler secret list'
  }
};

// CLI state
let globalOptions = {
  environment: 'dev',
  outputPath: null,
  outputFormat: 'json',
  isVerbose: false,
  isQuiet: false,
  isDryRun: false,
  help: false
};

/**
 * Display usage information and examples
 */
function showHelp() {
  console.log(`
Remote State Fetcher for Cloudflare Resources
============================================

Fetches current state from Cloudflare using wrangler CLI commands and normalizes
the output for SOT comparison.

USAGE:
  fetch-remote-state [OPTIONS]

OPTIONS:
  --env ENV              Environment to fetch state for (dev/stg/prod) [default: dev]
  --output PATH          Output directory for state files [default: ./generated]
  --format FORMAT        Output format (json) [default: json]
  --verbose              Enable verbose output
  --quiet                Suppress output except errors
  --dry-run              Show what would be done without executing
  --help                 Show this help message

EXAMPLES:
  # Fetch dev environment state
  fetch-remote-state --env dev

  # Fetch production state with verbose output
  fetch-remote-state --env prod --verbose

  # Dry run to see what would be fetched
  fetch-remote-state --env stg --dry-run

  # Output to specific directory
  fetch-remote-state --env dev --output ./state-backup/

OUTPUT FORMAT:
  The script generates a normalized JSON structure:
  {
    "environment": "dev",
    "timestamp": "2025-09-27T20:30:00.000Z",
    "account": {
      "id": "account-id",
      "name": "account-name"
    },
    "r2": {
      "buckets": [
        {"name": "bucket1", "binding": "BUCKET1"}
      ]
    },
    "workers": [
      {"name": "worker1", "script": "src/worker.ts"}
    ],
    "secrets": [
      {"name": "SECRET_NAME"}
    ]
  }
`);
}

/**
 * Parse command line arguments
 */
function parseArguments() {
  const args = process.argv.slice(2);

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    switch (arg) {
      case '--env':
        globalOptions.environment = args[++i];
        if (!CONFIG.supportedEnvironments.includes(globalOptions.environment)) {
          console.error(`❌ Error: Unsupported environment "${globalOptions.environment}"`);
          console.error(`   Supported: ${CONFIG.supportedEnvironments.join(', ')}`);
          process.exit(1);
        }
        break;
      case '--output':
        globalOptions.outputPath = args[++i];
        break;
      case '--format':
        globalOptions.outputFormat = args[++i];
        if (globalOptions.outputFormat !== 'json') {
          console.error(`❌ Error: Unsupported format "${globalOptions.outputFormat}"`);
          console.error(`   Supported: json`);
          process.exit(1);
        }
        break;
      case '--verbose':
        globalOptions.isVerbose = true;
        break;
      case '--quiet':
        globalOptions.isQuiet = true;
        break;
      case '--dry-run':
        globalOptions.isDryRun = true;
        break;
      case '--help':
        globalOptions.help = true;
        break;
      default:
        if (arg.startsWith('--')) {
          console.error(`❌ Error: Unknown option "${arg}"`);
          console.error('   Use --help to see available options');
          process.exit(1);
        }
        break;
    }
  }
}

/**
 * Log message if verbose mode is enabled
 */
function verbose(message) {
  if (globalOptions.isVerbose && !globalOptions.isQuiet) {
    console.log(`🔍 ${message}`);
  }
}

/**
 * Log info message unless quiet mode is enabled
 */
function info(message) {
  if (!globalOptions.isQuiet) {
    console.log(message);
  }
}

/**
 * Execute wrangler command with error handling
 */
function executeWranglerCommand(command, description) {
  verbose(`Executing: ${command}`);

  if (globalOptions.isDryRun) {
    info(`[DRY RUN] Would execute: ${command}`);
    return null;
  }

  try {
    // Add environment parameter if needed
    const envCommand = globalOptions.environment !== 'dev' ?
      `${command} --env ${globalOptions.environment}` : command;

    const output = execSync(envCommand, {
      encoding: 'utf8',
      timeout: 30000,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    verbose(`${description} completed successfully`);
    return output.trim();
  } catch (error) {
    if (error.status === 1 && error.stderr) {
      // Wrangler command failed
      console.error(`❌ Error executing ${description}:`);
      console.error(`   Command: ${command}`);
      console.error(`   Error: ${error.stderr.trim()}`);
    } else if (error.code === 'ENOENT') {
      console.error(`❌ Error: wrangler command not found`);
      console.error(`   Make sure wrangler is installed and available in PATH`);
    } else {
      console.error(`❌ Error executing ${description}: ${error.message}`);
    }
    return null;
  }
}

/**
 * Parse wrangler whoami output
 */
function parseWhoamiOutput(output) {
  if (!output) return null;

  const lines = output.split('\n');
  const result = {};

  for (const line of lines) {
    if (line.includes('Account ID:')) {
      result.id = line.split('Account ID:')[1].trim();
    } else if (line.includes('Account Name:')) {
      result.name = line.split('Account Name:')[1].trim();
    }
  }

  return Object.keys(result).length > 0 ? result : null;
}

/**
 * Parse R2 bucket list output
 */
function parseR2BucketsOutput(output) {
  if (!output) return [];

  const lines = output.split('\n');
  const buckets = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('│') && !trimmed.startsWith('┌') &&
        !trimmed.startsWith('├') && !trimmed.startsWith('└') &&
        !trimmed.includes('Name') && trimmed !== '') {
      // Extract bucket name (first column in table output)
      const bucketName = trimmed.split(/\s+/)[0];
      if (bucketName && bucketName !== 'Name') {
        buckets.push({
          name: bucketName,
          binding: bucketName.toUpperCase().replace(/-/g, '_')
        });
      }
    }
  }

  return buckets;
}

/**
 * Parse worker deployments output
 */
function parseWorkersOutput(output) {
  if (!output) return [];

  const lines = output.split('\n');
  const workers = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('│') && !trimmed.startsWith('┌') &&
        !trimmed.startsWith('├') && !trimmed.startsWith('└') &&
        !trimmed.includes('Script') && trimmed !== '') {
      // Extract worker name (first column in table output)
      const workerName = trimmed.split(/\s+/)[0];
      if (workerName && workerName !== 'Script') {
        workers.push({
          name: workerName,
          script: `src/${workerName}.ts` // Assume TypeScript files
        });
      }
    }
  }

  return workers;
}

/**
 * Parse secrets list output
 */
function parseSecretsOutput(output) {
  if (!output) return [];

  const lines = output.split('\n');
  const secrets = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('│') && !trimmed.startsWith('┌') &&
        !trimmed.startsWith('├') && !trimmed.startsWith('└') &&
        !trimmed.includes('Secret') && trimmed !== '') {
      // Extract secret name (first column in table output)
      const secretName = trimmed.split(/\s+/)[0];
      if (secretName && secretName !== 'Secret') {
        secrets.push({
          name: secretName
        });
      }
    }
  }

  return secrets;
}

/**
 * Fetch remote state from Cloudflare
 */
function fetchRemoteState() {
  info(`🌍 Fetching remote state for environment: ${globalOptions.environment}`);

  // Initialize state object
  const state = {
    environment: globalOptions.environment,
    timestamp: new Date().toISOString(),
    account: null,
    r2: {
      buckets: []
    },
    workers: [],
    secrets: []
  };

  // Fetch account information
  verbose('Fetching account information...');
  const whoamiOutput = executeWranglerCommand(
    CONFIG.wranglerCommands.whoami,
    'account information fetch'
  );
  state.account = parseWhoamiOutput(whoamiOutput);

  // Fetch R2 buckets
  verbose('Fetching R2 buckets...');
  const r2Output = executeWranglerCommand(
    CONFIG.wranglerCommands.listR2Buckets,
    'R2 buckets list'
  );
  state.r2.buckets = parseR2BucketsOutput(r2Output);

  // Fetch Workers
  verbose('Fetching Workers deployments...');
  const workersOutput = executeWranglerCommand(
    CONFIG.wranglerCommands.listWorkers,
    'Workers deployments list'
  );
  state.workers = parseWorkersOutput(workersOutput);

  // Fetch Secrets (optional, might fail if no workers deployed)
  verbose('Fetching secrets...');
  const secretsOutput = executeWranglerCommand(
    CONFIG.wranglerCommands.listSecrets,
    'secrets list'
  );
  state.secrets = parseSecretsOutput(secretsOutput);

  return state;
}

/**
 * Write state to output file
 */
function writeStateToFile(state) {
  const outputDir = globalOptions.outputPath || CONFIG.defaultOutputDir;

  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    if (globalOptions.isDryRun) {
      info(`[DRY RUN] Would create directory: ${outputDir}`);
    } else {
      fs.mkdirSync(outputDir, { recursive: true });
      verbose(`Created output directory: ${outputDir}`);
    }
  }

  const filename = `${globalOptions.environment}-${CONFIG.outputFilename}`;
  const outputPath = path.join(outputDir, filename);

  if (globalOptions.isDryRun) {
    info(`[DRY RUN] Would write state to: ${outputPath}`);
    info(`[DRY RUN] State content preview:`);
    console.log(JSON.stringify(state, null, 2));
    return outputPath;
  }

  try {
    fs.writeFileSync(outputPath, JSON.stringify(state, null, 2));
    info(`✅ Remote state written to: ${outputPath}`);

    // Show summary
    if (!globalOptions.isQuiet) {
      console.log(`\n📊 Summary:`);
      console.log(`   Environment: ${state.environment}`);
      console.log(`   Account: ${state.account?.name || 'Unknown'} (${state.account?.id || 'N/A'})`);
      console.log(`   R2 Buckets: ${state.r2.buckets.length}`);
      console.log(`   Workers: ${state.workers.length}`);
      console.log(`   Secrets: ${state.secrets.length}`);
    }

    return outputPath;
  } catch (error) {
    console.error(`❌ Error writing state file: ${error.message}`);
    process.exit(1);
  }
}

/**
 * Main execution function
 */
function main() {
  try {
    parseArguments();

    if (globalOptions.help) {
      showHelp();
      return;
    }

    // Validate environment
    if (!CONFIG.supportedEnvironments.includes(globalOptions.environment)) {
      console.error(`❌ Error: Invalid environment "${globalOptions.environment}"`);
      console.error(`   Supported environments: ${CONFIG.supportedEnvironments.join(', ')}`);
      process.exit(1);
    }

    // Fetch and write state
    const state = fetchRemoteState();
    writeStateToFile(state);

  } catch (error) {
    console.error(`❌ Fatal error: ${error.message}`);
    if (globalOptions.isVerbose) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Execute if run directly
if (require.main === module) {
  main();
}

module.exports = {
  fetchRemoteState,
  parseWhoamiOutput,
  parseR2BucketsOutput,
  parseWorkersOutput,
  parseSecretsOutput
};