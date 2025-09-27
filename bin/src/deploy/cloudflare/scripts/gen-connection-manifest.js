#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * R2 Connection Manifest Generator CLI
 *
 * A robust CLI interface for generating environment-specific R2 connection manifests.
 * Supports multiple environments (dev/stg/prod) with comprehensive validation,
 * error handling, and integration with SOPS encrypted secrets.
 *
 * Usage:
 *   gen-connection-manifest --env dev
 *   gen-connection-manifest --env prod --output ./config/ --verbose
 *   gen-connection-manifest --env stg --dry-run
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const sopsYaml = require('../helpers/sops-yaml.js');

// Configuration constants
const CONFIG = {
  supportedEnvironments: ['dev', 'stg', 'prod'],
  defaultOutputDir: './manifests',
  defaultRegion: 'auto',
  defaultConnectionMode: 'workers-binding',
  manifestVersion: '1.0.0',
  schemaPath: './schemas/r2-manifest.json',
  validatorScript: './scripts/validate-r2-manifest.sh'
};

// CLI state
let globalOptions = {
  environment: null,
  outputPath: null,
  isDryRun: false,
  isVerbose: false,
  isQuiet: false,
  forceOverwrite: false,
  useTemplate: false,
  help: false,
  listEnvironments: false
};

/**
 * Display usage information and examples
 */
function showHelp() {
  console.log(`
R2 Connection Manifest Generator CLI

DESCRIPTION:
    Generate environment-specific R2 connection manifests for Cloudflare R2 buckets.
    Supports encrypted secrets via SOPS and comprehensive validation.

USAGE:
    gen-connection-manifest [OPTIONS]

REQUIRED OPTIONS:
    --env <ENV>         Environment to generate manifest for (dev|stg|prod)

OPTIONAL OPTIONS:
    --output <PATH>     Output directory for manifest files (default: ./manifests)
    --dry-run           Preview generation without writing files
    --verbose           Enable verbose logging and progress indicators
    --quiet             Suppress all non-error output
    --force             Overwrite existing manifest files without confirmation
    --use-template      Use template values instead of encrypted secrets (for testing)
    --list-environments List supported environments and exit
    --help              Show this help message

EXAMPLES:
    # Basic usage - generate development environment manifest
    gen-connection-manifest --env dev

    # Production with custom output directory
    gen-connection-manifest --env prod --output ./config/r2/

    # Preview staging configuration without writing files
    gen-connection-manifest --env stg --dry-run --verbose

    # Force overwrite existing production manifest
    gen-connection-manifest --env prod --force

    # Test with template data (no encrypted secrets required)
    gen-connection-manifest --env dev --use-template --dry-run

    # List all supported environments
    gen-connection-manifest --list-environments

OUTPUT:
    Generated manifests follow the pattern: r2.<environment>.json
    Examples: r2.dev.json, r2.stg.json, r2.prod.json

INTEGRATION:
    # Validate generated manifest
    ./scripts/validate-r2-manifest.sh ./manifests/r2.dev.json

    # Use in Nix/Just workflows
    just r2:gen-manifest dev
    nix run .#gen-r2-manifest -- --env prod

PREREQUISITES:
    For encrypted secrets mode (default):
    - .sops.yaml configuration file
    - secrets/r2.<env>.yaml encrypted with SOPS
    - ~/.config/sops/age/keys.txt Age key file

    For template mode (testing):
    - No prerequisites, uses placeholder values

ERROR CODES:
    0  Success
    1  Invalid arguments or environment
    2  Missing prerequisites (secrets, keys)
    3  Validation failed
    4  I/O error (file operations)
    5  External command failed (SOPS, validation)
`);
}

/**
 * List supported environments
 */
function listEnvironments() {
  console.log('Supported environments:');
  CONFIG.supportedEnvironments.forEach(env => {
    const secretsFile = `secrets/r2.${env}.yaml`;
    const exists = fs.existsSync(secretsFile);
    const status = exists ? '✓' : '✗';
    console.log(`  ${env.padEnd(8)} ${status} ${exists ? 'secrets configured' : 'secrets missing'}`);
  });

  console.log('\nTo configure secrets for an environment:');
  console.log('  1. Copy template: cp secrets/r2.yaml.example secrets/r2.<env>.yaml');
  console.log('  2. Edit secrets: just secrets-edit secrets/r2.<env>.yaml');
}

/**
 * Parse command line arguments
 */
function parseArguments() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('❌ Error: No arguments provided. Use --help for usage information.');
    process.exit(1);
  }

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    switch (arg) {
      case '--env':
        if (i + 1 >= args.length) {
          console.error('❌ Error: --env requires a value (dev|stg|prod)');
          process.exit(1);
        }
        globalOptions.environment = args[++i];
        break;

      case '--output':
        if (i + 1 >= args.length) {
          console.error('❌ Error: --output requires a path value');
          process.exit(1);
        }
        globalOptions.outputPath = args[++i];
        break;

      case '--dry-run':
        globalOptions.isDryRun = true;
        break;

      case '--verbose':
        globalOptions.isVerbose = true;
        globalOptions.isQuiet = false;
        break;

      case '--quiet':
        globalOptions.isQuiet = true;
        globalOptions.isVerbose = false;
        break;

      case '--force':
        globalOptions.forceOverwrite = true;
        break;

      case '--use-template':
        globalOptions.useTemplate = true;
        break;

      case '--list-environments':
        globalOptions.listEnvironments = true;
        break;

      case '--help':
      case '-h':
        globalOptions.help = true;
        break;

      default:
        console.error(`❌ Error: Unknown option '${arg}'. Use --help for usage information.`);
        process.exit(1);
    }
  }
}

/**
 * Validate parsed arguments
 */
function validateArguments() {
  // Handle special options first
  if (globalOptions.help) {
    showHelp();
    process.exit(0);
  }

  if (globalOptions.listEnvironments) {
    listEnvironments();
    process.exit(0);
  }

  // Validate required environment option
  if (!globalOptions.environment) {
    console.error('❌ Error: --env is required. Use --help for usage information.');
    process.exit(1);
  }

  // Validate environment value
  if (!CONFIG.supportedEnvironments.includes(globalOptions.environment)) {
    console.error(`❌ Error: Invalid environment '${globalOptions.environment}'.`);
    console.error(`   Supported environments: ${CONFIG.supportedEnvironments.join(', ')}`);
    console.error('   Use --list-environments to see configuration status.');
    process.exit(1);
  }

  // Set default output path if not provided
  if (!globalOptions.outputPath) {
    globalOptions.outputPath = CONFIG.defaultOutputDir;
  }

  // Validate output path is not a file
  if (fs.existsSync(globalOptions.outputPath) && fs.statSync(globalOptions.outputPath).isFile()) {
    console.error(`❌ Error: Output path '${globalOptions.outputPath}' is a file, not a directory.`);
    process.exit(4);
  }
}

/**
 * Logging utilities
 */
function log(message, level = 'info') {
  if (globalOptions.isQuiet && level !== 'error') return;

  const prefix = {
    info: '📋',
    success: '✅',
    warning: '⚠️ ',
    error: '❌',
    verbose: '🔍',
    progress: '⏳'
  };

  if (level === 'verbose' && !globalOptions.isVerbose) return;

  console.log(`${prefix[level] || ''} ${message}`);
}

/**
 * Progress indicator for long operations
 */
function withProgress(message, operation) {
  if (!globalOptions.isQuiet) {
    process.stdout.write(`⏳ ${message}...`);
  }

  try {
    const result = operation();
    if (!globalOptions.isQuiet) {
      process.stdout.write(' ✅\n');
    }
    return result;
  } catch (error) {
    if (!globalOptions.isQuiet) {
      process.stdout.write(' ❌\n');
    }
    throw error;
  }
}

/**
 * Expand user home directory in file paths
 */
function expandPath(filePath) {
  if (filePath.startsWith('~/')) {
    return path.join(process.env.HOME, filePath.slice(2));
  }
  return filePath;
}

/**
 * Check prerequisites for SOT configuration
 */
async function checkPrerequisites() {
  if (globalOptions.useTemplate) {
    log('Using template mode - skipping prerequisites check', 'verbose');
    return;
  }

  log('Checking SOT prerequisites using shared helper', 'verbose');

  try {
    // Check if SOT file exists for the environment
    const sotPath = `spec/${globalOptions.environment}/cloudflare.yaml`;

    if (!fs.existsSync(sotPath)) {
      console.error(`❌ Error: SOT configuration file not found: ${sotPath}`);
      console.error('\nSolutions:');
      console.error('   1. Create SOT file: cp spec/dev/cloudflare.yaml spec/{env}/cloudflare.yaml');
      console.error('   2. Validate SOT format with JSON schema');
      console.error('   3. Or use --use-template for testing');
      process.exit(2);
    }

    // Use shared helper's health check for SOPS (needed for encrypted SOT files)
    const health = await sopsYaml.healthCheck();

    if (health.errors.length > 0) {
      log('SOPS prerequisites check found issues (may be OK for unencrypted SOT files):', 'warning');
      health.errors.forEach(error => {
        log(`   - ${error}`, 'warning');
      });
    } else {
      log('All SOPS prerequisites verified', 'success');
    }

    log(`SOT file exists: ${sotPath}`, 'success');

  } catch (error) {
    console.error('❌ Error: Prerequisites check failed:', error.message);
    process.exit(2);
  }
}

/**
 * Read R2 configuration from SOT (Single Source of Truth)
 */
async function readR2Configuration() {
  // Configure SOPS helper logging level
  if (globalOptions.isVerbose) {
    sopsYaml.setLogLevel('DEBUG');
  } else if (globalOptions.isQuiet) {
    sopsYaml.setLogLevel('ERROR');
  } else {
    sopsYaml.setLogLevel('INFO');
  }

  try {
    log('Reading SOT configuration using shared SOPS helper', 'verbose');

    // Use SOT configuration instead of legacy environment config
    const sotConfig = await sopsYaml.getSOTConfig(
      globalOptions.environment,
      {
        schema: sopsYaml.schemas.sot,
        cacheTTL: 2 * 60 * 1000 // 2 minutes cache for connection manifest
      }
    );

    // Validate SOT has R2 configuration
    if (!sotConfig.r2 || !sotConfig.r2.buckets) {
      throw new Error('SOT configuration missing r2.buckets section');
    }

    log('SOT configuration loaded successfully', 'verbose');
    return sotConfig;

  } catch (error) {
    console.error(`❌ Error: Failed to read SOT configuration`);
    console.error(`   ${error.message}`);

    if (!globalOptions.useTemplate) {
      console.error('\nSolutions:');
      console.error('   1. Ensure SOT file exists: spec/{env}/cloudflare.yaml');
      console.error('   2. Validate SOT format with JSON schema');
      console.error('   3. Or use --use-template for testing');
    }

    process.exit(2);
  }
}

/**
 * Generate R2 bucket configurations from SOT format
 */
function generateBucketConfigs(sotR2Config) {
  if (!sotR2Config || !sotR2Config.buckets || !Array.isArray(sotR2Config.buckets)) {
    throw new Error('Invalid SOT R2 configuration: buckets array missing');
  }

  const buckets = sotR2Config.buckets;
  log(`Generating configurations for ${buckets.length} buckets from SOT`, 'verbose');

  return buckets.map(bucket => {
    // Validate required SOT bucket fields
    if (!bucket.name || !bucket.binding) {
      console.error(`❌ Error: SOT bucket missing required name or binding field`);
      process.exit(3);
    }

    const bucketName = bucket.name;

    // Basic validation
    if (!/^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$/.test(bucketName)) {
      console.error(`❌ Error: Invalid bucket name '${bucketName}'`);
      console.error('   Bucket names must follow S3 naming conventions');
      process.exit(3);
    }

    if (bucketName.length < 3 || bucketName.length > 63) {
      console.error(`❌ Error: Bucket name '${bucketName}' must be 3-63 characters long`);
      process.exit(3);
    }

    log(`  - ${bucketName} (binding: ${bucket.binding})`, 'verbose');

    return {
      name: bucketName,
      binding: bucket.binding,
      public: bucketName.includes('public') || bucketName.includes('static'),
      ...(bucketName.includes('static') && {
        cors_origins: ['https://*.example.com', 'https://localhost:*']
      })
    };
  });
}

/**
 * Generate the complete R2 connection manifest from SOT
 */
async function generateManifest() {
  log('Generating R2 connection manifest from SOT', 'info');

  const sotConfig = await readR2Configuration();
  const buckets = generateBucketConfigs(sotConfig.r2);

  // Account ID should come from environment or encrypted secrets
  // SOT contains resource definitions, not sensitive credentials
  const accountId = process.env.CF_ACCOUNT_ID || 'placeholder-account-id';

  if (accountId === 'placeholder-account-id') {
    log('Using placeholder account ID - set CF_ACCOUNT_ID environment variable for production', 'warning');
  }

  const manifest = {
    account_id: accountId,
    endpoint: `https://${accountId}.r2.cloudflarestorage.com`,
    region: CONFIG.defaultRegion,
    buckets: buckets,
    connection_mode: CONFIG.defaultConnectionMode,
    meta: {
      environment: globalOptions.environment,
      version: CONFIG.manifestVersion,
      sot_version: sotConfig.version || 'unknown',
      created_at: new Date().toISOString(),
      description: `R2 connection manifest for ${globalOptions.environment} environment (SOT-driven)`
    }
  };

  // Add workers information if present in SOT
  if (sotConfig.workers && Array.isArray(sotConfig.workers)) {
    log(`Including workers metadata from SOT (${sotConfig.workers.length} workers)`, 'verbose');
    manifest.meta.workers_count = sotConfig.workers.length;
    manifest.meta.workers = sotConfig.workers.map(w => ({
      name: w.name,
      script: w.script || 'unknown',
      r2_bindings: w.bindings?.r2?.length || 0
    }));
  }

  // Credentials for S3 API mode would come from environment variables or encrypted secrets
  const accessKeyId = process.env.R2_ACCESS_KEY_ID;
  const secretAccessKey = process.env.R2_SECRET_ACCESS_KEY;
  const sessionToken = process.env.R2_SESSION_TOKEN;

  if (accessKeyId && secretAccessKey) {
    log('Including S3 API credentials from environment', 'verbose');
    manifest.credentials = {
      access_key_id: accessKeyId,
      secret_access_key: secretAccessKey,
      ...(sessionToken && { session_token: sessionToken })
    };
    manifest.connection_mode = 'hybrid';
  }

  return manifest;
}

/**
 * Validate generated manifest using external validator
 */
function validateManifest(manifest) {
  if (!fs.existsSync(CONFIG.validatorScript)) {
    log('Validation script not found - skipping validation', 'warning');
    return;
  }

  log('Validating generated manifest', 'verbose');

  return withProgress('Running manifest validation', () => {
    // Write temporary manifest for validation
    const tempFile = `/tmp/r2-manifest-${Date.now()}.json`;
    fs.writeFileSync(tempFile, JSON.stringify(manifest, null, 2));

    try {
      execSync(`${CONFIG.validatorScript} ${tempFile}`, { stdio: 'pipe' });
      log('Manifest validation passed', 'success');
    } catch (error) {
      console.error('❌ Error: Manifest validation failed');
      console.error(error.stdout.toString());
      process.exit(3);
    } finally {
      // Clean up temporary file
      if (fs.existsSync(tempFile)) {
        fs.unlinkSync(tempFile);
      }
    }
  });
}

/**
 * Write manifest to output file
 */
function writeManifest(manifest) {
  const fileName = `r2.${globalOptions.environment}.json`;
  const outputFile = path.join(globalOptions.outputPath, fileName);

  // Create output directory if it doesn't exist
  if (!globalOptions.isDryRun) {
    fs.mkdirSync(globalOptions.outputPath, { recursive: true });
  }

  // Check for existing file
  if (fs.existsSync(outputFile) && !globalOptions.forceOverwrite && !globalOptions.isDryRun) {
    console.error(`❌ Error: Output file ${outputFile} already exists.`);
    console.error('   Use --force to overwrite or choose a different output path.');
    process.exit(4);
  }

  const manifestJson = JSON.stringify(manifest, null, 2);

  if (globalOptions.isDryRun) {
    log('DRY RUN MODE - manifest content:', 'info');
    console.log('─'.repeat(80));
    console.log(manifestJson);
    console.log('─'.repeat(80));
    log(`Would write to: ${outputFile}`, 'info');
  } else {
    return withProgress(`Writing manifest to ${outputFile}`, () => {
      // Create backup if file exists
      if (fs.existsSync(outputFile)) {
        fs.copyFileSync(outputFile, `${outputFile}.backup`);
        log(`Backup created: ${outputFile}.backup`, 'info');
      }

      fs.writeFileSync(outputFile, manifestJson);
      log(`Manifest written to ${outputFile}`, 'success');
    });
  }
}

/**
 * Display summary information
 */
function showSummary(manifest) {
  log('SOT-Driven Generation Summary:', 'info');
  log(`  Environment: ${manifest.meta.environment}`, 'info');
  log(`  SOT Version: ${manifest.meta.sot_version}`, 'info');
  log(`  Account ID: ${manifest.account_id === 'placeholder-account-id' ? 'placeholder (set CF_ACCOUNT_ID)' : manifest.account_id.substring(0, 10) + '...'}`, 'info');
  log(`  Endpoint: ${manifest.endpoint}`, 'info');
  log(`  Connection Mode: ${manifest.connection_mode}`, 'info');
  log(`  Buckets (${manifest.buckets.length}):`, 'info');

  manifest.buckets.forEach(bucket => {
    const visibility = bucket.public ? 'public' : 'private';
    log(`    - ${bucket.name} (${visibility}, binding: ${bucket.binding})`, 'info');
  });

  if (manifest.meta.workers_count) {
    log(`  Workers (${manifest.meta.workers_count}):`, 'info');
    manifest.meta.workers.forEach(worker => {
      log(`    - ${worker.name} (${worker.r2_bindings} R2 bindings)`, 'info');
    });
  }

  if (!globalOptions.isDryRun) {
    log('Next Steps:', 'info');
    log(`  1. Review: cat ${path.join(globalOptions.outputPath, `r2.${globalOptions.environment}.json`)}`, 'info');
    log(`  2. Validate: ./scripts/validate-r2-manifest.sh ${path.join(globalOptions.outputPath, `r2.${globalOptions.environment}.json`)}`, 'info');
    log('  3. Set environment variables: CF_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY', 'info');
    log('  4. Deploy: Use manifest in your application configuration', 'info');
  }
}

/**
 * Main execution function
 */
async function main() {
  try {
    parseArguments();
    validateArguments();

    log(`Generating R2 connection manifest for ${globalOptions.environment} environment`, 'info');
    if (globalOptions.isDryRun) {
      log('Running in DRY RUN mode - no files will be written', 'warning');
    }

    await checkPrerequisites();
    const manifest = await generateManifest();
    validateManifest(manifest);
    writeManifest(manifest);
    showSummary(manifest);

    if (!globalOptions.isDryRun) {
      log('R2 connection manifest generation completed successfully!', 'success');
    }

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    if (globalOptions.isVerbose) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Execute if called directly
if (require.main === module) {
  main();
}

module.exports = {
  generateManifest,
  validateArguments,
  CONFIG
};