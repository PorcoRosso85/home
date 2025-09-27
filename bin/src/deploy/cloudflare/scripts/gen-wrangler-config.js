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
 * Read R2 configuration from SOT or legacy encrypted secrets
 */
async function readR2Config() {
  // Configure SOPS helper logging level
  sopsYaml.setLogLevel('WARN'); // Keep quiet for wrangler config generation

  try {
    console.log('📖 Reading R2 configuration using SOT-driven approach...');

    // Use SOT configuration (defaults to 'dev')
    const environment = 'dev'; // Could be made configurable
    const sotConfig = await sopsYaml.getSOTConfig(
      environment,
      {
        schema: sopsYaml.schemas.sot,
        cacheTTL: 10 * 60 * 1000 // 10 minutes cache for wrangler config
      }
    );

    // Extract R2 configuration from SOT
    if (!sotConfig.r2 || !sotConfig.r2.buckets) {
      throw new Error('SOT configuration missing r2.buckets section');
    }

    console.log(`✓ SOT Version: ${sotConfig.version || 'unknown'}`);
    console.log(`✓ R2 Buckets: ${sotConfig.r2.buckets.length} configured`);

    return sotConfig;

  } catch (error) {
    console.error('❌ Failed to read SOT configuration:', error.message);

    if (!useTemplate) {
      console.error('\nSolutions:');
      console.error('   1. Check SOT file exists: spec/dev/cloudflare.yaml');
      console.error('   2. Validate SOT format with JSON schema');
      console.error('   3. Or use --use-template for testing');
    }

    process.exit(1);
  }
}

/**
 * Generate R2 buckets configuration from SOT format
 */
function generateR2BucketsConfig(sotR2Config) {
  if (!sotR2Config || !sotR2Config.buckets || !Array.isArray(sotR2Config.buckets)) {
    throw new Error('Invalid SOT R2 configuration: buckets array missing');
  }

  return sotR2Config.buckets.map(bucket => {
    if (!bucket.name || !bucket.binding) {
      throw new Error('SOT R2 bucket missing required name or binding field');
    }

    return {
      binding: bucket.binding,
      bucket_name: bucket.name,
      preview_bucket_name: `${bucket.name}-preview`
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
 * Generate the complete wrangler.jsonc configuration from SOT
 */
async function generateConfig() {
  const sotConfig = await readR2Config();
  const existing = readExistingConfig();

  // Extract R2 configuration from SOT
  const r2BucketsConfig = generateR2BucketsConfig(sotConfig.r2);

  // For now, we'll use a placeholder account_id since SOT doesn't include secrets
  // In production, this would come from encrypted secrets or environment variables
  const accountId = process.env.CF_ACCOUNT_ID || existing.account_id || 'placeholder-account-id';

  // Build the complete configuration
  const wranglerConfig = {
    $schema: 'node_modules/wrangler/config-schema.json',
    name: existing.name || CONFIG.defaultName,
    main: existing.main || CONFIG.defaultMain,
    compatibility_date: CONFIG.compatibilityDate,
    compatibility_flags: CONFIG.compatibilityFlags,
    account_id: accountId,
    assets: {
      directory: CONFIG.assetsDirectory,
      binding: CONFIG.assetsBinding
    },
    observability: {
      enabled: true
    },
    r2_buckets: r2BucketsConfig
  };

  // Add workers configuration if present in SOT
  if (sotConfig.workers && Array.isArray(sotConfig.workers)) {
    console.log(`✓ Workers: ${sotConfig.workers.length} configured in SOT`);
    // Note: workers configuration would be handled separately in multi-worker setups
  }

  // Preserve existing configurations
  if (existing.d1_databases) {
    wranglerConfig.d1_databases = existing.d1_databases;
  }

  if (existing.durable_objects) {
    wranglerConfig.durable_objects = existing.durable_objects;
  }

  if (existing.vars) {
    wranglerConfig.vars = existing.vars;
  }

  if (existing.migrations) {
    wranglerConfig.migrations = existing.migrations;
  }

  return wranglerConfig;
}

/**
 * Main execution
 */
async function main() {
  try {
    const wranglerConfig = await generateConfig();
    const configJson = JSON.stringify(wranglerConfig, null, 2);

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
      console.log('✅ Generated wrangler.jsonc with SOT-driven R2 configuration');
    }

    // Show configured buckets from SOT
    console.log('');
    console.log('📋 R2 Buckets configured (from SOT):');
    wranglerConfig.r2_buckets.forEach(bucket => {
      console.log(`  - Binding: ${bucket.binding} → Bucket: ${bucket.bucket_name}`);
    });

    if (!isDryRun) {
      console.log('');
      console.log('🎯 Next steps:');
      console.log('  1. Review generated wrangler.jsonc');
      console.log('  2. Set CF_ACCOUNT_ID environment variable if needed');
      console.log('  3. Run "just r2:test" to test R2 connection locally');
      console.log('  4. Validate SOT configuration: "just sot:validate dev"');
    }

  } catch (error) {
    console.error('❌ SOT-driven configuration generation failed:', error.message);
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