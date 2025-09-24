#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * Basic functionality test for SOPS YAML helper
 * Tests core features without requiring full environment setup
 */

console.log('🧪 Testing SOPS YAML Helper Basic Functionality');

try {
  // Test module import
  const sopsYaml = require('./helpers/sops-yaml.js');
  console.log('✅ Module imported successfully');

  // Test exports
  const requiredExports = ['decrypt', 'getEnvironmentConfig', 'schemas', 'CONFIG', 'healthCheck'];
  for (const exportName of requiredExports) {
    if (!(exportName in sopsYaml)) {
      throw new Error(`Missing export: ${exportName}`);
    }
  }
  console.log('✅ All required exports present');

  // Test configuration
  if (sopsYaml.CONFIG.defaultCacheTTL && sopsYaml.CONFIG.maxCacheSize) {
    console.log('✅ Configuration object valid');
  } else {
    throw new Error('Configuration object invalid');
  }

  // Test schemas
  if (sopsYaml.schemas.r2 && sopsYaml.schemas.r2.required) {
    console.log('✅ R2 schema present and valid');
  } else {
    throw new Error('R2 schema invalid');
  }

  // Test cache functionality
  sopsYaml.clearCache();
  const stats = sopsYaml.getCacheStats();
  if (stats.size === 0 && stats.hits === 0) {
    console.log('✅ Cache functionality working');
  } else {
    throw new Error('Cache functionality failed');
  }

  // Test logging
  sopsYaml.setLogLevel('ERROR');
  console.log('✅ Logging level setting works');

  // Test template mode (should work without SOPS setup)
  (async () => {
    try {
      const config = await sopsYaml.getEnvironmentConfig('r2', 'dev', true);
      if (config.cf_account_id && config.r2_buckets) {
        console.log('✅ Template mode works');
        console.log(`   Account ID: ${config.cf_account_id.substring(0, 10)}...`);
        console.log(`   Buckets: ${config.r2_buckets}`);
      } else {
        throw new Error('Template config incomplete');
      }

      // Test health check
      const health = await sopsYaml.healthCheck();
      console.log('✅ Health check works');
      console.log(`   SOPS available: ${health.sops}`);
      console.log(`   Age key: ${health.ageKey}`);

      console.log('\n🎉 All basic tests passed!');
      console.log('\nThe shared SOPS YAML helper is ready for use by both generators.');

    } catch (asyncError) {
      console.error('❌ Async test failed:', asyncError.message);
      process.exit(1);
    }
  })();

} catch (error) {
  console.error('❌ Basic test failed:', error.message);
  process.exit(1);
}