#!/usr/bin/env node

/**
 * Safe wrangler.jsonc generator with R2 configuration
 * Handles JSONC parsing and generation properly
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const sopsYaml = require('../helpers/sops-yaml.js');

// Configuration
const CONFIG = {
  defaultName: 'redwoodsdk-r2-local',
  defaultMain: 'src/worker.ts',
  compatibilityDate: new Date().toISOString().split('T')[0],
  compatibilityFlags: ['nodejs_compat'],
  assetsDirectory: './dist/client',
  assetsBinding: 'ASSETS'
};

// Command line argument parsing
const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
const useTemplate = args.includes('--use-template');

if (args.includes('-h') || args.includes('--help')) {
  console.log(`
Usage: node gen-wrangler-config.js [OPTIONS]

Generate wrangler.jsonc with R2 configuration

OPTIONS:
    --dry-run       Show what would be generated without writing files
    --use-template  Use template values instead of encrypted secrets
    -h, --help      Show this help message

EXAMPLES:
    node gen-wrangler-config.js                  # Generate using encrypted secrets
    node gen-wrangler-config.js --dry-run       # Preview generation
    node gen-wrangler-config.js --use-template  # Use template values for testing
`);
  process.exit(0);
}

console.log('🔧 Generating wrangler.jsonc with R2 configuration...');
if (isDryRun) {
  console.log('   (DRY RUN MODE - no files will be modified)');
}

/**
 * Safe JSONC parser that handles comments and trailing commas
 */
function parseJSONC(content) {
  try {
    // Simple JSONC parsing - remove comments and trailing commas
    const cleaned = content
      .replace(/\/\*[\s\S]*?\*\//g, '') // Remove /* */ comments
      .replace(/\/\/.*$/gm, '')         // Remove // comments
      .replace(/,(\s*[}\]])/g, '$1');   // Remove trailing commas

    return JSON.parse(cleaned);
  } catch (error) {
    console.warn('⚠️  Failed to parse existing JSONC, using defaults');
    return {};
  }
}

/**
 * Read R2 configuration from encrypted secrets or templates
 */
async function readR2Config() {
  // Configure SOPS helper logging level
  sopsYaml.setLogLevel('WARN'); // Keep quiet for wrangler config generation

  try {
    console.log('📖 Reading R2 configuration using shared SOPS helper...');

    // Use shared helper with environment detection (defaults to 'dev')
    const environment = 'dev'; // Could be made configurable
    const config = await sopsYaml.getEnvironmentConfig(
      'r2',
      environment,
      useTemplate,
      {
        schema: sopsYaml.schemas.r2,
        cacheTTL: 10 * 60 * 1000 // 10 minutes cache for wrangler config
      }
    );

    console.log(`✓ CF_ACCOUNT_ID: ${config.cf_account_id.substring(0, 10)}...`);
    console.log(`✓ R2_BUCKETS: ${config.r2_buckets}`);

    return config;

  } catch (error) {
    console.error('❌ Failed to read R2 configuration:', error.message);

    if (!useTemplate) {
      console.error('\nSolutions:');
      console.error('   1. Initialize secrets: nix run .#secrets-init');
      console.error('   2. Configure secrets: nix run .#secrets-edit -- secrets/r2.yaml');
      console.error('   3. Or use --use-template for testing');
    }

    process.exit(1);
  }
}

/**
 * Generate R2 buckets configuration
 */
function generateR2BucketsConfig(r2BucketsString) {
  const buckets = r2BucketsString.split(',').map(b => b.trim());

  return buckets.map(bucket => {
    const bindingName = bucket.toUpperCase().replace(/-/g, '_');
    return {
      binding: bindingName,
      bucket_name: bucket,
      preview_bucket_name: `${bucket}-preview`
    };
  });
}

/**
 * Read existing wrangler.jsonc configuration
 */
function readExistingConfig() {
  if (!fs.existsSync('wrangler.jsonc')) {
    return {};
  }

  console.log('📖 Reading existing wrangler.jsonc configuration...');

  try {
    const content = fs.readFileSync('wrangler.jsonc', 'utf8');
    const existing = parseJSONC(content);
    console.log('✓ Preserved existing configuration');
    return existing;
  } catch (error) {
    console.warn('⚠️  Failed to parse existing wrangler.jsonc, using defaults');
    return {};
  }
}

/**
 * Generate the complete wrangler.jsonc configuration
 */
async function generateConfig() {
  const config = await readR2Config();
  const existing = readExistingConfig();

  const { cf_account_id, r2_buckets } = config;

  // Generate R2 buckets configuration
  const r2BucketsConfig = generateR2BucketsConfig(r2_buckets);

  // Build the complete configuration
  const config = {
    $schema: 'node_modules/wrangler/config-schema.json',
    name: existing.name || CONFIG.defaultName,
    main: existing.main || CONFIG.defaultMain,
    compatibility_date: CONFIG.compatibilityDate,
    compatibility_flags: CONFIG.compatibilityFlags,
    account_id: cf_account_id,
    assets: {
      directory: CONFIG.assetsDirectory,
      binding: CONFIG.assetsBinding
    },
    observability: {
      enabled: true
    },
    r2_buckets: r2BucketsConfig
  };

  // Preserve existing configurations
  if (existing.d1_databases) {
    config.d1_databases = existing.d1_databases;
  }

  if (existing.durable_objects) {
    config.durable_objects = existing.durable_objects;
  }

  if (existing.vars) {
    config.vars = existing.vars;
  }

  if (existing.migrations) {
    config.migrations = existing.migrations;
  }

  return config;
}

/**
 * Main execution
 */
async function main() {
  try {
    const config = await generateConfig();
    const configJson = JSON.stringify(config, null, 2);

    if (isDryRun) {
      console.log('');
      console.log('📋 Generated wrangler.jsonc content (DRY RUN):');
      console.log('=============================================');
      console.log(configJson);
    } else {
      // Create backup if file exists
      if (fs.existsSync('wrangler.jsonc')) {
        fs.copyFileSync('wrangler.jsonc', 'wrangler.jsonc.backup');
        console.log('✓ Backed up existing wrangler.jsonc');
      }

      // Write the new configuration
      fs.writeFileSync('wrangler.jsonc', configJson);
      console.log('✅ Generated wrangler.jsonc with R2 configuration');
    }

    // Show configured buckets
    console.log('');
    console.log('📋 R2 Buckets configured:');
    config.r2_buckets.forEach(bucket => {
      console.log(`  - Binding: ${bucket.binding} → Bucket: ${bucket.bucket_name}`);
    });

    if (!isDryRun) {
      console.log('');
      console.log('🎯 Next steps:');
      console.log('  1. Review generated wrangler.jsonc');
      console.log('  2. Run "just r2:test" to test R2 connection locally');
      console.log('  3. Run "just r2:check-secrets" to verify security');
    }

  } catch (error) {
    console.error('❌ Configuration generation failed:', error.message);
    process.exit(1);
  }
}

// Helper function for path expansion
path.expandUser = function(filePath) {
  if (filePath.startsWith('~/')) {
    return path.join(process.env.HOME, filePath.slice(2));
  }
  return filePath;
};

main().catch(error => {
  console.error('❌ Unexpected error:', error.message);
  process.exit(1);
});