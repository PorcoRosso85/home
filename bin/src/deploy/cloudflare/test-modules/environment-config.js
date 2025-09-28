/**
 * Environment-Specific Configuration Tests
 *
 * Tests configuration generation and validation for different environments
 * (dev, staging, production) ensuring proper isolation, security levels,
 * and environment-specific customizations.
 *
 * Test scenarios:
 * - Development environment configuration
 * - Staging environment configuration
 * - Production environment configuration
 * - Environment isolation and security
 * - Configuration inheritance and overrides
 * - Environment validation rules
 */

const fs = require('fs');
const path = require('path');

/**
 * Run environment configuration tests
 */
async function runTests(testSuite) {
  const { logger } = testSuite;

  logger.info('Running Environment-Specific Configuration Tests...');

  // Test 1: Development Environment Configuration
  await testSuite.runTest('Development Environment Configuration', async () => {
    await testDevelopmentEnvironment(testSuite);
  }, { category: 'ENV_CONFIG' });

  // Test 2: Staging Environment Configuration
  await testSuite.runTest('Staging Environment Configuration', async () => {
    await testStagingEnvironment(testSuite);
  }, { category: 'ENV_CONFIG' });

  // Test 3: Production Environment Configuration
  await testSuite.runTest('Production Environment Configuration', async () => {
    await testProductionEnvironment(testSuite);
  }, { category: 'ENV_CONFIG' });

  // Test 4: Environment Isolation Validation
  await testSuite.runTest('Environment Isolation Validation', async () => {
    await testEnvironmentIsolation(testSuite);
  }, { category: 'ENV_CONFIG' });

  // Test 5: Configuration Inheritance and Overrides
  await testSuite.runTest('Configuration Inheritance and Overrides', async () => {
    await testConfigurationInheritance(testSuite);
  }, { category: 'ENV_CONFIG' });

  // Test 6: Environment-Specific Security Rules
  await testSuite.runTest('Environment-Specific Security Rules', async () => {
    await testEnvironmentSecurityRules(testSuite);
  }, { category: 'ENV_CONFIG' });

  // Test 7: Cross-Environment Validation
  await testSuite.runTest('Cross-Environment Validation', async () => {
    await testCrossEnvironmentValidation(testSuite);
  }, { category: 'ENV_CONFIG' });

  // Test 8: Environment Migration Scenarios
  await testSuite.runTest('Environment Migration Scenarios', async () => {
    await testEnvironmentMigration(testSuite);
  }, { category: 'ENV_CONFIG' });

  // Test 9: Environment-Specific Feature Flags
  await testSuite.runTest('Environment-Specific Feature Flags', async () => {
    await testEnvironmentFeatureFlags(testSuite);
  }, { category: 'ENV_CONFIG' });
}

/**
 * Test development environment configuration
 */
async function testDevelopmentEnvironment(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing development environment configuration...');

  const manifestGen = require('../scripts/gen-connection-manifest.js');
  const manifest = await manifestGen.generateManifest({
    environment: 'dev',
    useTemplate: true,
    dryRun: true
  });

  // Verify development-specific settings
  if (manifest.meta.environment !== 'dev') {
    throw new Error('Development manifest has incorrect environment');
  }

  // Development should allow more permissive settings
  if (manifest.connection_mode === 'workers-binding') {
    // This is expected for development
    logger.debug('Development using workers-binding mode');
  }

  // Check development-specific bucket configuration
  if (!manifest.buckets || manifest.buckets.length === 0) {
    throw new Error('Development environment missing bucket configuration');
  }

  // Development buckets should have appropriate naming
  const devBuckets = manifest.buckets.filter(bucket =>
    bucket.name.includes('dev') || bucket.name.includes('development')
  );

  if (devBuckets.length === 0 && !process.env.ALLOW_GENERIC_BUCKET_NAMES) {
    logger.warn('Development buckets should ideally include "dev" or "development" in names');
  }

  // Verify development endpoint format
  if (!manifest.endpoint || !manifest.endpoint.includes('.r2.cloudflarestorage.com')) {
    throw new Error('Development manifest has invalid R2 endpoint');
  }

  // Development configuration should be non-production
  if (manifest.meta.description && manifest.meta.description.toLowerCase().includes('production')) {
    throw new Error('Development configuration should not reference production');
  }

  // Test wrangler configuration for development
  const wranglerGen = require('../scripts/gen-wrangler-config.js');
  const wranglerConfig = await wranglerGen.generateWranglerConfig({
    environment: 'dev',
    manifest: manifest,
    dryRun: true
  });

  // Development should have appropriate wrangler settings
  if (wranglerConfig.env && wranglerConfig.env.dev) {
    // Check development-specific environment variables
    const devEnv = wranglerConfig.env.dev;
    if (!devEnv.vars) {
      throw new Error('Development environment missing environment variables');
    }
  }

  logger.debug('Development environment configuration validated successfully');
}

/**
 * Test staging environment configuration
 */
async function testStagingEnvironment(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing staging environment configuration...');

  const manifestGen = require('../scripts/gen-connection-manifest.js');
  const manifest = await manifestGen.generateManifest({
    environment: 'stg',
    useTemplate: true,
    dryRun: true
  });

  // Verify staging-specific settings
  if (manifest.meta.environment !== 'stg') {
    throw new Error('Staging manifest has incorrect environment');
  }

  // Staging should have production-like but separate configuration
  if (!manifest.buckets || manifest.buckets.length === 0) {
    throw new Error('Staging environment missing bucket configuration');
  }

  // Staging buckets should have appropriate naming
  const stagingBuckets = manifest.buckets.filter(bucket =>
    bucket.name.includes('stg') ||
    bucket.name.includes('staging') ||
    bucket.name.includes('stage')
  );

  if (stagingBuckets.length === 0 && !process.env.ALLOW_GENERIC_BUCKET_NAMES) {
    logger.warn('Staging buckets should ideally include "stg", "staging", or "stage" in names');
  }

  // Staging should have appropriate security settings
  if (manifest.connection_mode === 's3-api' && !manifest.credentials) {
    throw new Error('Staging S3 API mode requires credentials configuration');
  }

  // Test staging-specific bucket configurations
  for (const bucket of manifest.buckets) {
    // Staging buckets should generally not be public unless specifically needed
    if (bucket.public && !bucket.name.includes('public')) {
      logger.warn(`Staging bucket "${bucket.name}" is public - verify this is intentional`);
    }

    // CORS should be configured appropriately for staging
    if (bucket.cors_origins && bucket.cors_origins.some(origin => origin.includes('localhost'))) {
      logger.warn('Staging bucket has localhost CORS origins - should use staging domains');
    }
  }

  // Test wrangler configuration for staging
  const wranglerGen = require('../scripts/gen-wrangler-config.js');
  const wranglerConfig = await wranglerGen.generateWranglerConfig({
    environment: 'stg',
    manifest: manifest,
    dryRun: true
  });

  // Staging should have proper environment configuration
  if (wranglerConfig.env && wranglerConfig.env.staging) {
    const stagingEnv = wranglerConfig.env.staging;
    if (!stagingEnv.vars || !stagingEnv.vars.R2_ACCOUNT_ID) {
      throw new Error('Staging environment missing required variables');
    }
  }

  logger.debug('Staging environment configuration validated successfully');
}

/**
 * Test production environment configuration
 */
async function testProductionEnvironment(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing production environment configuration...');

  const manifestGen = require('../scripts/gen-connection-manifest.js');
  const manifest = await manifestGen.generateManifest({
    environment: 'prod',
    useTemplate: true,
    dryRun: true
  });

  // Verify production-specific settings
  if (manifest.meta.environment !== 'prod') {
    throw new Error('Production manifest has incorrect environment');
  }

  // Production should have strict configuration requirements
  if (!manifest.buckets || manifest.buckets.length === 0) {
    throw new Error('Production environment missing bucket configuration');
  }

  // Production buckets should follow naming conventions
  for (const bucket of manifest.buckets) {
    // Production bucket names should not contain dev/test references
    if (bucket.name.includes('dev') || bucket.name.includes('test') || bucket.name.includes('temp')) {
      throw new Error(`Production bucket "${bucket.name}" contains non-production naming`);
    }

    // Verify bucket name follows production standards
    if (!bucket.name.match(/^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$/)) {
      throw new Error(`Production bucket "${bucket.name}" has invalid naming format`);
    }

    // Production buckets should have appropriate security
    if (bucket.public) {
      if (!bucket.custom_domain) {
        logger.warn(`Production public bucket "${bucket.name}" should have custom domain`);
      }

      if (!bucket.cors_origins || bucket.cors_origins.length === 0) {
        logger.warn(`Production public bucket "${bucket.name}" should have CORS configuration`);
      }
    }
  }

  // Production should use appropriate connection mode
  if (manifest.connection_mode === 's3-api' && !manifest.credentials) {
    throw new Error('Production S3 API mode requires credentials configuration');
  }

  // Production endpoint should be properly configured
  if (!manifest.endpoint || !manifest.endpoint.includes('.r2.cloudflarestorage.com')) {
    throw new Error('Production manifest has invalid R2 endpoint');
  }

  // Production account ID should be valid format
  if (!manifest.account_id.match(/^[a-f0-9]{32}$/)) {
    throw new Error('Production account ID has invalid format');
  }

  // Test wrangler configuration for production
  const wranglerGen = require('../scripts/gen-wrangler-config.js');
  const wranglerConfig = await wranglerGen.generateWranglerConfig({
    environment: 'prod',
    manifest: manifest,
    dryRun: true
  });

  // Production should have comprehensive configuration
  if (!wranglerConfig.name || wranglerConfig.name.includes('dev') || wranglerConfig.name.includes('test')) {
    throw new Error('Production wrangler config has non-production name');
  }

  // Production should have proper compatibility date
  if (!wranglerConfig.compatibility_date) {
    throw new Error('Production configuration missing compatibility date');
  }

  // Verify production date is not too old
  const compatDate = new Date(wranglerConfig.compatibility_date);
  const oneYearAgo = new Date();
  oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);

  if (compatDate < oneYearAgo) {
    logger.warn('Production compatibility date is more than one year old - consider updating');
  }

  logger.debug('Production environment configuration validated successfully');
}

/**
 * Test environment isolation validation
 */
async function testEnvironmentIsolation(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing environment isolation...');

  const environments = ['dev', 'stg', 'prod'];
  const manifests = {};

  // Generate manifests for all environments
  const manifestGen = require('../scripts/gen-connection-manifest.js');

  for (const env of environments) {
    manifests[env] = await manifestGen.generateManifest({
      environment: env,
      useTemplate: true,
      dryRun: true
    });
  }

  // Verify environment isolation
  for (let i = 0; i < environments.length; i++) {
    for (let j = i + 1; j < environments.length; j++) {
      const env1 = environments[i];
      const env2 = environments[j];
      const manifest1 = manifests[env1];
      const manifest2 = manifests[env2];

      // Environments should have different metadata
      if (manifest1.meta.environment === manifest2.meta.environment) {
        throw new Error(`Environments ${env1} and ${env2} have same metadata environment`);
      }

      // Account IDs should be different (in template mode, they should be environment-specific)
      if (manifest1.account_id === manifest2.account_id && !process.env.ALLOW_SHARED_ACCOUNT_ID) {
        logger.warn(`Environments ${env1} and ${env2} share same account ID - verify isolation`);
      }

      // Bucket configurations should be isolated
      const buckets1 = manifest1.buckets.map(b => b.name);
      const buckets2 = manifest2.buckets.map(b => b.name);
      const sharedBuckets = buckets1.filter(name => buckets2.includes(name));

      if (sharedBuckets.length > 0 && !process.env.ALLOW_SHARED_BUCKETS) {
        throw new Error(`Environments ${env1} and ${env2} share buckets: ${sharedBuckets.join(', ')}`);
      }

      // Endpoints should be environment-specific
      if (manifest1.endpoint === manifest2.endpoint && !process.env.ALLOW_SHARED_ENDPOINTS) {
        logger.warn(`Environments ${env1} and ${env2} share same endpoint - verify isolation`);
      }
    }
  }

  // Test configuration isolation through helpers
  const sopsHelper = require('../helpers/sops-yaml.js');
  sopsHelper.clearCache();

  const configs = {};
  for (const env of environments) {
    configs[env] = await sopsHelper.getEnvironmentConfig('r2', env, true);
  }

  // Verify helper provides isolated configurations
  for (let i = 0; i < environments.length; i++) {
    for (let j = i + 1; j < environments.length; j++) {
      const env1 = environments[i];
      const env2 = environments[j];
      const config1 = configs[env1];
      const config2 = configs[env2];

      if (JSON.stringify(config1) === JSON.stringify(config2)) {
        throw new Error(`Helper provides identical configurations for ${env1} and ${env2}`);
      }
    }
  }

  logger.debug('Environment isolation validated successfully');
}

/**
 * Test configuration inheritance and overrides
 */
async function testConfigurationInheritance(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing configuration inheritance...');

  const sopsHelper = require('../helpers/sops-yaml.js');

  // Test base configuration inheritance
  const baseConfig = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

  // Verify base configuration has required fields
  const requiredBaseFields = ['cf_account_id', 'r2_buckets'];
  for (const field of requiredBaseFields) {
    if (!baseConfig[field]) {
      throw new Error(`Base configuration missing required field: ${field}`);
    }
  }

  // Test environment-specific overrides
  const environments = ['dev', 'stg', 'prod'];
  const configs = {};

  for (const env of environments) {
    configs[env] = await sopsHelper.getEnvironmentConfig('r2', env, true);

    // Each environment should have the base fields
    for (const field of requiredBaseFields) {
      if (!configs[env][field]) {
        throw new Error(`Environment ${env} missing inherited field: ${field}`);
      }
    }
  }

  // Test that overrides work properly
  if (configs.dev.cf_account_id === configs.prod.cf_account_id) {
    logger.warn('Dev and prod environments use same account ID - verify this is intentional');
  }

  // Test bucket inheritance and overrides
  const devBuckets = configs.dev.r2_buckets;
  const prodBuckets = configs.prod.r2_buckets;

  if (Array.isArray(devBuckets) && Array.isArray(prodBuckets)) {
    // Development might have different buckets than production
    const hasSharedBuckets = devBuckets.some(bucket => prodBuckets.includes(bucket));
    if (hasSharedBuckets && !process.env.ALLOW_SHARED_BUCKETS) {
      logger.warn('Dev and prod environments share bucket names - verify isolation');
    }
  }

  // Test configuration merging behavior
  const manifestGen = require('../scripts/gen-connection-manifest.js');

  // Test with custom overrides
  const customManifest = await manifestGen.generateManifest({
    environment: 'dev',
    useTemplate: true,
    dryRun: true,
    overrides: {
      region: 'eeur',
      connection_mode: 's3-api'
    }
  });

  if (customManifest.region !== 'eeur') {
    throw new Error('Configuration overrides not applied correctly');
  }

  if (customManifest.connection_mode !== 's3-api') {
    throw new Error('Connection mode override not applied correctly');
  }

  logger.debug('Configuration inheritance validated successfully');
}

/**
 * Test environment-specific security rules
 */
async function testEnvironmentSecurityRules(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing environment security rules...');

  const environments = ['dev', 'stg', 'prod'];
  const manifestGen = require('../scripts/gen-connection-manifest.js');

  for (const env of environments) {
    const manifest = await manifestGen.generateManifest({
      environment: env,
      useTemplate: true,
      dryRun: true
    });

    // Test environment-specific security requirements
    if (env === 'prod') {
      // Production should have stricter security
      for (const bucket of manifest.buckets) {
        if (bucket.public && !bucket.custom_domain) {
          throw new Error(`Production public bucket "${bucket.name}" should have custom domain`);
        }

        if (bucket.cors_origins && bucket.cors_origins.includes('*')) {
          throw new Error(`Production bucket "${bucket.name}" should not allow wildcard CORS`);
        }
      }

      // Production should not use insecure connection modes
      if (manifest.connection_mode === 'workers-binding' && manifest.credentials) {
        logger.warn('Production using workers-binding with explicit credentials - review security');
      }
    }

    if (env === 'dev') {
      // Development can be more permissive but should still be secure
      for (const bucket of manifest.buckets) {
        if (bucket.public && bucket.cors_origins && bucket.cors_origins.includes('*')) {
          logger.warn(`Development bucket "${bucket.name}" allows wildcard CORS - use specific origins in production`);
        }
      }
    }

    // All environments should have valid account IDs
    if (!manifest.account_id.match(/^[a-f0-9]{32}$/)) {
      throw new Error(`Environment ${env} has invalid account ID format`);
    }

    // All environments should have secure endpoints
    if (!manifest.endpoint.startsWith('https://')) {
      throw new Error(`Environment ${env} uses insecure endpoint`);
    }
  }

  // Test security validation integration
  try {
    const securityResult = await testSuite.execCommand('nix run .#no-plaintext-secrets');
    if (securityResult.code !== 0) {
      logger.warn('Security validation found issues - review configuration');
    }
  } catch (error) {
    logger.debug(`Security validation check: ${error.message}`);
  }

  logger.debug('Environment security rules validated successfully');
}

/**
 * Test cross-environment validation
 */
async function testCrossEnvironmentValidation(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing cross-environment validation...');

  const environments = ['dev', 'stg', 'prod'];
  const manifests = {};
  const wranglerConfigs = {};

  const manifestGen = require('../scripts/gen-connection-manifest.js');
  const wranglerGen = require('../scripts/gen-wrangler-config.js');

  // Generate all configurations
  for (const env of environments) {
    manifests[env] = await manifestGen.generateManifest({
      environment: env,
      useTemplate: true,
      dryRun: true
    });

    wranglerConfigs[env] = await wranglerGen.generateWranglerConfig({
      environment: env,
      manifest: manifests[env],
      dryRun: true
    });
  }

  // Validate consistency across environments
  for (const env of environments) {
    const manifest = manifests[env];
    const wranglerConfig = wranglerConfigs[env];

    // Manifest and wrangler config should be consistent
    if (wranglerConfig.vars.R2_ACCOUNT_ID !== manifest.account_id) {
      throw new Error(`Environment ${env} has account ID mismatch between manifest and wrangler config`);
    }

    if (wranglerConfig.vars.R2_ENDPOINT !== manifest.endpoint) {
      throw new Error(`Environment ${env} has endpoint mismatch between manifest and wrangler config`);
    }

    // Environment should be properly labeled
    if (manifest.meta.environment !== env) {
      throw new Error(`Environment ${env} manifest has incorrect environment label`);
    }
  }

  // Test schema validation across environments
  const schema = JSON.parse(fs.readFileSync('../schemas/r2-manifest.json', 'utf8'));
  const Ajv = require('ajv');
  const ajv = new Ajv();
  const validate = ajv.compile(schema);

  for (const env of environments) {
    if (!validate(manifests[env])) {
      throw new Error(`Environment ${env} manifest fails schema validation: ${JSON.stringify(validate.errors)}`);
    }
  }

  // Test configuration evolution (dev → stg → prod)
  const devManifest = manifests.dev;
  const stagingManifest = manifests.stg;
  const prodManifest = manifests.prod;

  // Development should be most permissive
  if (devManifest.buckets.some(b => b.public) &&
      !stagingManifest.buckets.some(b => b.public) &&
      prodManifest.buckets.some(b => b.public)) {
    logger.warn('Inconsistent public bucket configuration across environments');
  }

  logger.debug('Cross-environment validation completed successfully');
}

/**
 * Test environment migration scenarios
 */
async function testEnvironmentMigration(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing environment migration scenarios...');

  const manifestGen = require('../scripts/gen-connection-manifest.js');

  // Test migration from dev to staging
  const devManifest = await manifestGen.generateManifest({
    environment: 'dev',
    useTemplate: true,
    dryRun: true
  });

  const stagingManifest = await manifestGen.generateManifest({
    environment: 'stg',
    useTemplate: true,
    dryRun: true,
    migrateFrom: 'dev'
  });

  // Staging should maintain compatible structure with dev
  if (devManifest.buckets.length > stagingManifest.buckets.length) {
    logger.warn('Staging has fewer buckets than development - verify migration path');
  }

  // Test bucket naming migration
  const devBucketNames = devManifest.buckets.map(b => b.name);
  const stagingBucketNames = stagingManifest.buckets.map(b => b.name);

  for (const devBucket of devBucketNames) {
    const expectedStagingName = devBucket.replace('dev', 'stg');
    if (!stagingBucketNames.includes(expectedStagingName) &&
        !stagingBucketNames.includes(devBucket.replace('dev', 'staging'))) {
      logger.debug(`Dev bucket "${devBucket}" may need manual staging equivalent`);
    }
  }

  // Test configuration compatibility
  if (devManifest.connection_mode !== stagingManifest.connection_mode) {
    logger.warn('Connection mode differs between dev and staging - verify compatibility');
  }

  // Test staging to production migration
  const prodManifest = await manifestGen.generateManifest({
    environment: 'prod',
    useTemplate: true,
    dryRun: true,
    migrateFrom: 'stg'
  });

  // Production should be compatible with staging
  if (stagingManifest.region !== prodManifest.region) {
    logger.warn('Region differs between staging and production - verify migration impact');
  }

  logger.debug('Environment migration scenarios tested successfully');
}

/**
 * Test environment-specific feature flags
 */
async function testEnvironmentFeatureFlags(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing environment feature flags...');

  const wranglerGen = require('../scripts/gen-wrangler-config.js');
  const environments = ['dev', 'stg', 'prod'];

  for (const env of environments) {
    const manifest = await require('../scripts/gen-connection-manifest.js').generateManifest({
      environment: env,
      useTemplate: true,
      dryRun: true
    });

    const wranglerConfig = await wranglerGen.generateWranglerConfig({
      environment: env,
      manifest: manifest,
      dryRun: true
    });

    // Test environment-specific feature flags
    if (env === 'dev') {
      // Development might have debug features enabled
      if (wranglerConfig.vars && wranglerConfig.vars.DEBUG_MODE !== 'true') {
        logger.debug('Development environment could enable debug mode');
      }
    }

    if (env === 'prod') {
      // Production should have performance optimizations
      if (wranglerConfig.vars && wranglerConfig.vars.DEBUG_MODE === 'true') {
        logger.warn('Production environment should not have debug mode enabled');
      }

      // Production should have monitoring enabled
      if (wranglerConfig.vars && !wranglerConfig.vars.MONITORING_ENABLED) {
        logger.warn('Production environment should have monitoring enabled');
      }
    }

    // Test compatibility flags
    if (wranglerConfig.compatibility_flags) {
      const flags = wranglerConfig.compatibility_flags;

      // Verify appropriate flags for environment
      if (env === 'prod' && flags.includes('experimental-flag')) {
        logger.warn(`Production environment using experimental flag - verify stability`);
      }
    }
  }

  logger.debug('Environment feature flags tested successfully');
}

module.exports = {
  runTests,
  testDevelopmentEnvironment,
  testStagingEnvironment,
  testProductionEnvironment,
  testEnvironmentIsolation,
  testConfigurationInheritance,
  testEnvironmentSecurityRules,
  testCrossEnvironmentValidation,
  testEnvironmentMigration,
  testEnvironmentFeatureFlags,
};
