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
 * Check prerequisites for encrypted secrets mode
 */
async function checkPrerequisites() {
  if (globalOptions.useTemplate) {
    log('Using template mode - skipping prerequisites check', 'verbose');
    return;
  }

  log('Checking SOPS prerequisites using shared helper', 'verbose');

  try {
    // Use shared helper's health check
    const health = await sopsYaml.healthCheck();

    if (health.errors.length > 0) {
      console.error('❌ Error: SOPS prerequisites check failed:');
      health.errors.forEach(error => {
        console.error(`   - ${error}`);
      });
      console.error('\nSolutions:');
      console.error('   1. Initialize secrets: just secrets-init');
      console.error('   2. Configure environment secrets: just secrets-edit');
      console.error('   3. Or use --use-template for testing');
      process.exit(2);
    }

    log('All SOPS prerequisites verified', 'success');

    // Additional check for environment-specific secrets file
    const envSecretsPattern = `secrets/r2/${globalOptions.environment}.yaml`;
    const fallbackSecretsPattern = `secrets/r2.yaml`;

    if (!fs.existsSync(envSecretsPattern) && !fs.existsSync(fallbackSecretsPattern)) {
      console.error(`❌ Error: No R2 secrets found for environment '${globalOptions.environment}'`);
      console.error(`   Expected: ${envSecretsPattern} or ${fallbackSecretsPattern}`);
      console.error('\nSolutions:');
      console.error('   1. Create secrets: just secrets-edit');
      console.error('   2. Use --list-environments to see status');
      process.exit(2);
    }

  } catch (error) {
    console.error('❌ Error: Prerequisites check failed:', error.message);
    process.exit(2);
  }
}

/**
 * Read R2 configuration from encrypted secrets or template
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
    log('Reading R2 configuration using shared SOPS helper', 'verbose');

    // Use the shared helper with validation
    const config = await sopsYaml.getEnvironmentConfig(
      'r2',
      globalOptions.environment,
      globalOptions.useTemplate,
      {
        schema: sopsYaml.schemas.r2,
        cacheTTL: 2 * 60 * 1000 // 2 minutes cache for connection manifest
      }
    );

    log('R2 configuration loaded successfully', 'verbose');
    return config;

  } catch (error) {
    console.error(`❌ Error: Failed to read R2 configuration`);
    console.error(`   ${error.message}`);

    if (!globalOptions.useTemplate) {
      console.error('\nSolutions:');
      console.error('   1. Initialize secrets: just secrets-init');
      console.error('   2. Configure environment secrets: just secrets-edit');
      console.error('   3. Or use --use-template for testing');
    }

    process.exit(2);
  }
}

/**
 * Generate R2 bucket configurations
 */
function generateBucketConfigs(bucketsString) {
  const buckets = bucketsString.split(',').map(b => b.trim()).filter(b => b);

  log(`Generating configurations for ${buckets.length} buckets`, 'verbose');

  return buckets.map(bucketName => {
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

    log(`  - ${bucketName}`, 'verbose');

    return {
      name: bucketName,
      public: bucketName.includes('public') || bucketName.includes('static'),
      ...(bucketName.includes('static') && {
        cors_origins: ['https://*.example.com', 'https://localhost:*']
      })
    };
  });
}

/**
 * Generate the complete R2 connection manifest
 */
async function generateManifest() {
  log('Generating R2 connection manifest', 'info');

  const config = await readR2Configuration();
  const buckets = generateBucketConfigs(config.r2_buckets);

  const manifest = {
    account_id: config.cf_account_id,
    endpoint: `https://${config.cf_account_id}.r2.cloudflarestorage.com`,
    region: CONFIG.defaultRegion,
    buckets: buckets,
    connection_mode: CONFIG.defaultConnectionMode,
    meta: {
      environment: globalOptions.environment,
      version: CONFIG.manifestVersion,
      created_at: new Date().toISOString(),
      description: `R2 connection manifest for ${globalOptions.environment} environment`
    }
  };

  // Add credentials for S3 API mode (if available)
  if (config.r2_access_key_id && config.r2_secret_access_key) {
    log('Including S3 API credentials', 'verbose');
    manifest.credentials = {
      access_key_id: config.r2_access_key_id,
      secret_access_key: config.r2_secret_access_key,
      ...(config.r2_session_token && { session_token: config.r2_session_token })
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
  log('Generation Summary:', 'info');
  log(`  Environment: ${manifest.meta.environment}`, 'info');
  log(`  Account ID: ${manifest.account_id.substring(0, 10)}...`, 'info');
  log(`  Endpoint: ${manifest.endpoint}`, 'info');
  log(`  Connection Mode: ${manifest.connection_mode}`, 'info');
  log(`  Buckets (${manifest.buckets.length}):`, 'info');

  manifest.buckets.forEach(bucket => {
    const visibility = bucket.public ? 'public' : 'private';
    log(`    - ${bucket.name} (${visibility})`, 'info');
  });

  if (!globalOptions.isDryRun) {
    log('Next Steps:', 'info');
    log(`  1. Review: cat ${path.join(globalOptions.outputPath, `r2.${globalOptions.environment}.json`)}`, 'info');
    log(`  2. Validate: ./scripts/validate-r2-manifest.sh ${path.join(globalOptions.outputPath, `r2.${globalOptions.environment}.json`)}`, 'info');
    log('  3. Deploy: Use manifest in your application configuration', 'info');
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