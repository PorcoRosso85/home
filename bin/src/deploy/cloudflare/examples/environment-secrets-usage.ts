#!/usr/bin/env tsx
/**
 * Example usage of environment-specific secrets for R2 configuration
 * Run with: npx tsx examples/environment-secrets-usage.ts
 */

import {
  loadR2ConfigForEnvironment,
  getAvailableEnvironments,
  generateR2ConnectionManifest,
  Environment
} from '../src/environment-secrets';

async function demonstrateEnvironmentSecrets() {
  console.log('🔐 Environment-Specific Secrets Demo\n');

  // 1. List available environments
  console.log('📋 Available environments:');
  const environments = getAvailableEnvironments();
  environments.forEach(env => {
    console.log(`  - ${env}`);
  });

  if (environments.length === 0) {
    console.log('  ⚠️  No environment secrets found.');
    console.log('  📝 Create them by copying templates:');
    console.log('     cp secrets/r2/dev.yaml.template secrets/r2/dev.yaml');
    console.log('     nix run .#secrets-edit -- secrets/r2/dev.yaml');
    return;
  }

  console.log('\n');

  // 2. Load configuration for each environment
  for (const env of environments) {
    console.log(`🔍 Loading configuration for: ${env}`);

    try {
      const config = await loadR2ConfigForEnvironment(env);

      console.log(`  ✅ Environment: ${config.environment}`);
      console.log(`  📝 Description: ${config.description}`);
      console.log(`  🏢 Account ID: ${config.cf_account_id}`);
      console.log(`  🪣 Buckets: ${config.r2_buckets.length} configured`);

      config.r2_buckets.forEach((bucket, index) => {
        console.log(`    ${index + 1}. ${bucket.name} (${bucket.purpose})`);
      });

      console.log(`  🔒 Security Level: ${getSecurityLevel(config)}`);
      console.log(`  📊 Monitoring: ${config.monitoring?.enable_metrics ? 'enabled' : 'disabled'}`);

      // 3. Generate connection manifest
      console.log('\n📄 Connection Manifest:');
      const manifest = await generateR2ConnectionManifest(env);
      console.log(JSON.stringify(manifest, null, 2));

    } catch (error) {
      console.error(`  ❌ Failed to load ${env}: ${error.message}`);
      console.log(`  💡 Make sure the file is encrypted with SOPS`);
    }

    console.log('\n' + '─'.repeat(50) + '\n');
  }
}

function getSecurityLevel(config: any): string {
  const security = config.security;

  if (security.require_auth && security.rate_limiting && security.encryption_at_rest) {
    return 'high 🔴';
  } else if (security.require_auth && security.rate_limiting) {
    return 'medium 🟡';
  } else {
    return 'low 🟢';
  }
}

// Example of environment-specific deployment logic
async function deployToEnvironment(env: Environment) {
  console.log(`🚀 Deploying to ${env} environment...\n`);

  try {
    const config = await loadR2ConfigForEnvironment(env);

    // Simulate deployment steps
    console.log('1. ✅ Loaded environment configuration');
    console.log(`2. 🔗 Connecting to account: ${config.cf_account_id}`);
    console.log('3. 🪣 Setting up R2 buckets:');

    config.r2_buckets.forEach(bucket => {
      console.log(`   - ${bucket.name}: ${bucket.public_access ? 'public' : 'private'}`);
    });

    console.log('4. 🔒 Applying security settings:');
    console.log(`   - Authentication: ${config.security.require_auth ? 'required' : 'optional'}`);
    console.log(`   - Rate limiting: ${config.security.rate_limiting ? 'enabled' : 'disabled'}`);

    if (config.monitoring?.enable_metrics) {
      console.log('5. 📊 Configuring monitoring and alerts');
    }

    console.log(`\n🎉 Deployment to ${env} completed successfully!`);

  } catch (error) {
    console.error(`❌ Deployment to ${env} failed: ${error.message}`);
    throw error;
  }
}

// Main execution
async function main() {
  const command = process.argv[2];

  switch (command) {
    case 'demo':
      await demonstrateEnvironmentSecrets();
      break;

    case 'deploy':
      const env = process.argv[3] as Environment;
      if (!env || !['dev', 'stg', 'prod'].includes(env)) {
        console.error('Usage: npm run example deploy <dev|stg|prod>');
        process.exit(1);
      }
      await deployToEnvironment(env);
      break;

    default:
      console.log('🔐 Environment Secrets Usage Examples\n');
      console.log('Available commands:');
      console.log('  demo    - Demonstrate loading all environments');
      console.log('  deploy  - Simulate deployment to specific environment');
      console.log('\nExamples:');
      console.log('  npx tsx examples/environment-secrets-usage.ts demo');
      console.log('  npx tsx examples/environment-secrets-usage.ts deploy dev');
      break;
  }
}

if (require.main === module) {
  main().catch(console.error);
}