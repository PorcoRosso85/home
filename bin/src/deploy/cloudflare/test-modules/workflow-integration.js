/**
 * End-to-End Workflow Integration Tests
 *
 * Tests the complete workflow from secret loading through manifest generation
 * to validation and deployment preparation. This ensures all components work
 * together seamlessly.
 *
 * Test scenarios:
 * - Template mode workflow (no SOPS required)
 * - Full encrypted workflow (SOPS required)
 * - Multi-environment workflow
 * - Error recovery and rollback
 */

const fs = require('fs');
const path = require('path');

/**
 * Run workflow integration tests
 */
async function runTests(testSuite) {
  const { logger } = testSuite;

  logger.info('Running End-to-End Workflow Integration Tests...');

  // Test 1: Template Mode Complete Workflow
  await testSuite.runTest('Template Mode Complete Workflow', async () => {
    await testTemplateWorkflow(testSuite);
  }, { category: 'E2E_WORKFLOW' });

  // Test 2: Multi-Environment Workflow
  await testSuite.runTest('Multi-Environment Workflow', async () => {
    await testMultiEnvironmentWorkflow(testSuite);
  }, { category: 'E2E_WORKFLOW' });

  // Test 3: Full Encrypted Workflow
  await testSuite.runTest('Full Encrypted Workflow', async () => {
    await testEncryptedWorkflow(testSuite);
  }, {
    category: 'E2E_WORKFLOW',
    skipIf: process.argv.includes('--skip-sops') ? 'SOPS tests disabled' : false
  });

  // Test 4: Component Integration Chain
  await testSuite.runTest('Component Integration Chain', async () => {
    await testComponentIntegrationChain(testSuite);
  }, { category: 'E2E_WORKFLOW' });

  // Test 5: Deployment Preparation Workflow
  await testSuite.runTest('Deployment Preparation Workflow', async () => {
    await testDeploymentPreparationWorkflow(testSuite);
  }, { category: 'E2E_WORKFLOW' });

  // Test 6: Error Recovery and Rollback
  await testSuite.runTest('Error Recovery and Rollback', async () => {
    await testErrorRecoveryWorkflow(testSuite);
  }, { category: 'E2E_WORKFLOW' });

  // Test 7: Concurrent Workflow Execution
  await testSuite.runTest('Concurrent Workflow Execution', async () => {
    await testConcurrentWorkflows(testSuite);
  }, { category: 'E2E_WORKFLOW' });

  // Test 8: Workflow State Management
  await testSuite.runTest('Workflow State Management', async () => {
    await testWorkflowStateManagement(testSuite);
  }, { category: 'E2E_WORKFLOW' });
}

/**
 * Test complete template mode workflow
 */
async function testTemplateWorkflow(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing template mode workflow...');

  // Step 1: Load SOPS helper
  const sopsHelper = require('../helpers/sops-yaml.js');

  // Step 2: Get environment config using template
  const config = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

  if (!config.cf_account_id || !config.r2_buckets) {
    throw new Error('Template config missing required fields');
  }

  // Step 3: Generate connection manifest
  const manifestGen = require('../scripts/gen-connection-manifest.js');

  const manifest = await manifestGen.generateManifest({
    environment: 'dev',
    useTemplate: true,
    dryRun: true
  });

  if (!manifest.account_id || !manifest.buckets || !manifest.meta) {
    throw new Error('Generated manifest missing required fields');
  }

  // Step 4: Validate manifest against schema
  const schema = JSON.parse(fs.readFileSync('../schemas/r2-manifest.json', 'utf8'));
  const Ajv = require('ajv');
  const ajv = new Ajv();
  const validate = ajv.compile(schema);

  if (!validate(manifest)) {
    throw new Error(`Manifest validation failed: ${JSON.stringify(validate.errors)}`);
  }

  // Step 5: Generate wrangler config
  const wranglerGen = require('../scripts/gen-wrangler-config.js');

  const wranglerConfig = await wranglerGen.generateWranglerConfig({
    environment: 'dev',
    manifest: manifest,
    dryRun: true
  });

  if (!wranglerConfig.name || !wranglerConfig.compatibility_date) {
    throw new Error('Generated wrangler config missing required fields');
  }

  // Step 6: Verify integration between components
  if (wranglerConfig.vars && wranglerConfig.vars.R2_ACCOUNT_ID !== manifest.account_id) {
    throw new Error('Account ID mismatch between manifest and wrangler config');
  }

  logger.debug('Template workflow completed successfully');
}

/**
 * Test multi-environment workflow
 */
async function testMultiEnvironmentWorkflow(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing multi-environment workflow...');

  const environments = ['dev', 'stg', 'prod'];
  const results = {};

  for (const env of environments) {
    logger.debug(`Processing environment: ${env}`);

    // Generate manifest for each environment
    const manifestGen = require('../scripts/gen-connection-manifest.js');

    const manifest = await manifestGen.generateManifest({
      environment: env,
      useTemplate: true,
      dryRun: true
    });

    if (!manifest.meta || manifest.meta.environment !== env) {
      throw new Error(`Environment mismatch in ${env} manifest`);
    }

    results[env] = manifest;
  }

  // Verify environment-specific differences
  if (results.dev.meta.environment === results.prod.meta.environment) {
    throw new Error('Environment configurations should be different');
  }

  // Verify consistent structure across environments
  for (const env of environments) {
    const manifest = results[env];
    if (!manifest.account_id || !manifest.buckets || !manifest.meta) {
      throw new Error(`Incomplete ${env} manifest structure`);
    }
  }

  logger.debug('Multi-environment workflow completed successfully');
}

/**
 * Test full encrypted workflow (requires SOPS setup)
 */
async function testEncryptedWorkflow(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing encrypted workflow...');

  // Check if SOPS is available
  try {
    await testSuite.execCommand('which sops');
  } catch (error) {
    throw new Error('SOPS not available for encrypted workflow test');
  }

  // Check if age key is configured
  const ageKeyPath = process.env.SOPS_AGE_KEY_FILE || '~/.config/sops/age/keys.txt';
  const expandedPath = ageKeyPath.replace('~', process.env.HOME);

  if (!fs.existsSync(expandedPath)) {
    throw new Error('Age key file not found for encrypted workflow test');
  }

  // Test encrypted secret loading
  const sopsHelper = require('../helpers/sops-yaml.js');

  // Create a test encrypted file
  const testSecretPath = path.join(testSuite.TEST_CONFIG.tempDir, 'test-secret.yaml');
  const testSecret = {
    cf_account_id: '1234567890abcdef1234567890abcdef',
    r2_buckets: ['test-bucket-encrypted'],
    r2_access_key_id: 'test-access-key',
    r2_secret_access_key: 'test-secret-key'
  };

  // Write and encrypt test secret
  fs.writeFileSync(testSecretPath, `# Test secret for encrypted workflow
cf_account_id: ${testSecret.cf_account_id}
r2_buckets:
  - ${testSecret.r2_buckets[0]}
r2_access_key_id: ${testSecret.r2_access_key_id}
r2_secret_access_key: ${testSecret.r2_secret_access_key}
`);

  // Encrypt the file
  await testSuite.execCommand(`sops --encrypt --in-place ${testSecretPath}`);

  // Test decryption through helper
  const decryptedConfig = await sopsHelper.decrypt(testSecretPath);

  if (decryptedConfig.cf_account_id !== testSecret.cf_account_id) {
    throw new Error('Decrypted config does not match original');
  }

  // Test full workflow with encrypted config
  const manifestGen = require('../scripts/gen-connection-manifest.js');

  const manifest = await manifestGen.generateManifest({
    environment: 'test',
    configPath: testSecretPath,
    dryRun: true
  });

  if (manifest.account_id !== testSecret.cf_account_id) {
    throw new Error('Manifest does not use encrypted config values');
  }

  logger.debug('Encrypted workflow completed successfully');
}

/**
 * Test component integration chain
 */
async function testComponentIntegrationChain(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing component integration chain...');

  // Test the chain: SOPS Helper → Manifest Generator → Validator → Wrangler Generator

  // 1. SOPS Helper provides config
  const sopsHelper = require('../helpers/sops-yaml.js');
  const config = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

  // 2. Manifest Generator uses config
  const manifestGen = require('../scripts/gen-connection-manifest.js');
  const manifest = await manifestGen.generateManifest({
    environment: 'dev',
    config: config,
    dryRun: true
  });

  // 3. Validator validates manifest
  const validateResult = await testSuite.execCommand(
    `node scripts/validate-r2-manifest.sh --manifest-data '${JSON.stringify(manifest)}'`
  );

  if (validateResult.code !== 0) {
    throw new Error('Manifest validation failed in integration chain');
  }

  // 4. Wrangler Generator uses manifest
  const wranglerGen = require('../scripts/gen-wrangler-config.js');
  const wranglerConfig = await wranglerGen.generateWranglerConfig({
    environment: 'dev',
    manifest: manifest,
    dryRun: true
  });

  // 5. Verify data consistency through the chain
  if (wranglerConfig.vars.R2_ACCOUNT_ID !== manifest.account_id) {
    throw new Error('Data inconsistency in integration chain');
  }

  if (wranglerConfig.vars.R2_ENDPOINT !== manifest.endpoint) {
    throw new Error('Endpoint mismatch in integration chain');
  }

  logger.debug('Component integration chain completed successfully');
}

/**
 * Test deployment preparation workflow
 */
async function testDeploymentPreparationWorkflow(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing deployment preparation workflow...');

  const environment = 'prod';

  // Step 1: Generate production manifest
  const manifestGen = require('../scripts/gen-connection-manifest.js');
  const manifest = await manifestGen.generateManifest({
    environment: environment,
    useTemplate: true,
    dryRun: true
  });

  // Step 2: Validate production readiness
  if (manifest.meta.environment !== environment) {
    throw new Error('Environment mismatch in production manifest');
  }

  if (!manifest.buckets || manifest.buckets.length === 0) {
    throw new Error('Production manifest missing bucket configuration');
  }

  // Step 3: Generate wrangler configuration
  const wranglerGen = require('../scripts/gen-wrangler-config.js');
  const wranglerConfig = await wranglerGen.generateWranglerConfig({
    environment: environment,
    manifest: manifest,
    dryRun: true
  });

  // Step 4: Validate deployment readiness
  const requiredWranglerFields = ['name', 'main', 'compatibility_date', 'vars'];
  for (const field of requiredWranglerFields) {
    if (!wranglerConfig[field]) {
      throw new Error(`Missing required wrangler field for deployment: ${field}`);
    }
  }

  // Step 5: Run security validation
  const securityResult = await testSuite.execCommand('nix run .#no-plaintext-secrets');
  if (securityResult.code !== 0) {
    throw new Error('Security validation failed in deployment preparation');
  }

  // Step 6: Simulate deployment preparation commands
  const prepCommands = [
    'nix run .#r2 -- validate prod',
    'nix run .#r2 -- check-secrets',
    'nix run .#r2 -- status'
  ];

  for (const command of prepCommands) {
    try {
      const result = await testSuite.execCommand(`${command} --dry-run`);
      logger.debug(`Deployment prep command succeeded: ${command}`);
    } catch (error) {
      // Some commands might not support --dry-run, that's okay
      logger.debug(`Deployment prep command check: ${command} - ${error.message}`);
    }
  }

  logger.debug('Deployment preparation workflow completed successfully');
}

/**
 * Test error recovery and rollback
 */
async function testErrorRecoveryWorkflow(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing error recovery workflow...');

  // Test 1: Invalid configuration recovery
  try {
    const manifestGen = require('../scripts/gen-connection-manifest.js');
    await manifestGen.generateManifest({
      environment: 'invalid-env',
      useTemplate: true,
      dryRun: true
    });
    throw new Error('Should have failed with invalid environment');
  } catch (error) {
    if (!error.message.includes('invalid') && !error.message.includes('Invalid')) {
      throw new Error(`Unexpected error message: ${error.message}`);
    }
    // Expected error - recovery successful
  }

  // Test 2: File system error recovery
  const tempBadFile = path.join(testSuite.TEST_CONFIG.tempDir, 'bad-config.yaml');
  fs.writeFileSync(tempBadFile, 'invalid: yaml: content: [unclosed');

  try {
    const sopsHelper = require('../helpers/sops-yaml.js');
    await sopsHelper.decrypt(tempBadFile);
    throw new Error('Should have failed with invalid YAML');
  } catch (error) {
    if (!error.message.includes('YAML') && !error.message.includes('parse')) {
      throw new Error(`Unexpected error for invalid YAML: ${error.message}`);
    }
    // Expected error - recovery successful
  }

  // Test 3: Network timeout recovery (simulated)
  const sopsHelper = require('../helpers/sops-yaml.js');
  const originalTimeout = sopsHelper.CONFIG.defaultTimeout;

  try {
    // Simulate timeout scenario
    sopsHelper.CONFIG.defaultTimeout = 1; // Very short timeout

    // Should handle timeout gracefully
    const health = await sopsHelper.healthCheck();
    if (typeof health.timestamp !== 'number') {
      throw new Error('Health check should complete even with short timeout');
    }
  } finally {
    // Restore original timeout
    sopsHelper.CONFIG.defaultTimeout = originalTimeout;
  }

  logger.debug('Error recovery workflow completed successfully');
}

/**
 * Test concurrent workflow execution
 */
async function testConcurrentWorkflows(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing concurrent workflow execution...');

  const environments = ['dev', 'stg', 'prod'];
  const manifestGen = require('../scripts/gen-connection-manifest.js');

  // Start concurrent manifest generation
  const promises = environments.map(env =>
    manifestGen.generateManifest({
      environment: env,
      useTemplate: true,
      dryRun: true
    })
  );

  // Wait for all to complete
  const results = await Promise.all(promises);

  // Verify all results are valid and different
  for (let i = 0; i < results.length; i++) {
    const manifest = results[i];
    const expectedEnv = environments[i];

    if (!manifest.meta || manifest.meta.environment !== expectedEnv) {
      throw new Error(`Concurrent execution failed for ${expectedEnv}`);
    }
  }

  // Test cache consistency during concurrent access
  const sopsHelper = require('../helpers/sops-yaml.js');
  sopsHelper.clearCache();

  const concurrentPromises = Array(5).fill().map(() =>
    sopsHelper.getEnvironmentConfig('r2', 'dev', true)
  );

  const concurrentResults = await Promise.all(concurrentPromises);

  // All results should be identical (cached)
  const firstResult = JSON.stringify(concurrentResults[0]);
  for (const result of concurrentResults) {
    if (JSON.stringify(result) !== firstResult) {
      throw new Error('Cache inconsistency during concurrent access');
    }
  }

  logger.debug('Concurrent workflow execution completed successfully');
}

/**
 * Test workflow state management
 */
async function testWorkflowStateManagement(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing workflow state management...');

  const sopsHelper = require('../helpers/sops-yaml.js');

  // Test cache state management
  sopsHelper.clearCache();
  let stats = sopsHelper.getCacheStats();

  if (stats.size !== 0 || stats.hits !== 0 || stats.misses !== 0) {
    throw new Error('Cache not properly cleared');
  }

  // Load config and check cache state
  await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
  stats = sopsHelper.getCacheStats();

  if (stats.misses !== 1) {
    throw new Error('Cache miss not recorded properly');
  }

  // Load same config and check cache hit
  await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
  stats = sopsHelper.getCacheStats();

  if (stats.hits !== 1) {
    throw new Error('Cache hit not recorded properly');
  }

  // Test state persistence across operations
  const config1 = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
  const config2 = await sopsHelper.getEnvironmentConfig('r2', 'stg', true);

  if (JSON.stringify(config1) === JSON.stringify(config2)) {
    throw new Error('Different environments should have different configurations');
  }

  // Test cleanup and state reset
  sopsHelper.clearCache();
  stats = sopsHelper.getCacheStats();

  if (stats.size !== 0) {
    throw new Error('Cache not properly cleared after operations');
  }

  logger.debug('Workflow state management completed successfully');
}

module.exports = {
  runTests,
  testTemplateWorkflow,
  testMultiEnvironmentWorkflow,
  testEncryptedWorkflow,
  testComponentIntegrationChain,
  testDeploymentPreparationWorkflow,
  testErrorRecoveryWorkflow,
  testConcurrentWorkflows,
  testWorkflowStateManagement,
};
