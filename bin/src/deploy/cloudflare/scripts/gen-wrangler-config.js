#!/usr/bin/env node

/**
 * Safe wrangler.jsonc generator with R2 configuration
 * Handles JSONC parsing and generation properly
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

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
function readR2Config() {
  if (useTemplate) {
    console.log('📖 Using template R2 configuration...');
    return {
      cf_account_id: 'demo-account-id-12345',
      r2_buckets: 'user-uploads,static-assets'
    };
  }

  // Check prerequisites for encrypted secrets mode
  const requiredFiles = [
    '.sops.yaml',
    'secrets/r2.yaml',
    path.expandUser('~/.config/sops/age/keys.txt')
  ];

  for (const file of requiredFiles) {
    if (!fs.existsSync(file)) {
      console.error(`❌ ${file} not found.`);
      if (file === '.sops.yaml' || file === 'secrets/r2.yaml') {
        console.error('   Run "nix run .#secrets-init" first.');
      }
      console.error('   Or use --use-template for testing.');
      process.exit(1);
    }
  }

  console.log('📖 Reading encrypted R2 configuration...');

  try {
    // Set SOPS environment
    process.env.SOPS_AGE_KEY_FILE = path.expandUser('~/.config/sops/age/keys.txt');

    // Decrypt and parse R2 configuration
    const decryptedYaml = execSync('sops -d secrets/r2.yaml', { encoding: 'utf8' });

    // Parse YAML (simple key: value parsing)
    const config = {};
    decryptedYaml.split('\n').forEach(line => {
      const match = line.match(/^([^#:]+):\s*(.+)$/);
      if (match) {
        const key = match[1].trim();
        const value = match[2].trim();
        config[key] = value;
      }
    });

    const cf_account_id = config.cf_account_id || 'your-account-id-here';
    const r2_buckets = config.r2_buckets || 'user-uploads,static-assets';

    if (cf_account_id === 'your-account-id-here') {
      console.warn('⚠️  Warning: CF_ACCOUNT_ID is placeholder. Update secrets/r2.yaml');
    }

    return { cf_account_id, r2_buckets };
  } catch (error) {
    console.error('❌ Failed to read encrypted secrets:', error.message);
    console.error('   Run "nix run .#secrets-edit -- secrets/r2.yaml" to set up secrets');
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
function generateConfig() {
  const { cf_account_id, r2_buckets } = readR2Config();
  const existing = readExistingConfig();

  console.log(`✓ CF_ACCOUNT_ID: ${cf_account_id.substring(0, 10)}...`);
  console.log(`✓ R2_BUCKETS: ${r2_buckets}`);

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
function main() {
  try {
    const config = generateConfig();
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

main();