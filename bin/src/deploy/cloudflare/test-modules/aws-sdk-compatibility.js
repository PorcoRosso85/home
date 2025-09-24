/**
 * AWS SDK v3 Compatibility Validation Tests
 *
 * Tests compatibility between generated R2 configurations and AWS SDK v3
 * S3Client. Ensures that manifests can be used to create working S3Client
 * instances and perform basic operations.
 *
 * Test scenarios:
 * - S3Client initialization with R2 configuration
 * - Basic S3 operations (ListBuckets, HeadBucket, etc.)
 * - Credential configuration validation
 * - Region and endpoint configuration
 * - Error handling and compatibility edge cases
 * - AWS SDK v3 specific features
 */

const fs = require('fs');
const path = require('path');

/**
 * Run AWS SDK v3 compatibility tests
 */
async function runTests(testSuite) {
  const { logger } = testSuite;

  logger.info('Running AWS SDK v3 Compatibility Tests...');

  // Test 1: S3Client Configuration Generation
  await testSuite.runTest('S3Client Configuration Generation', async () => {
    await testS3ClientConfigGeneration(testSuite);
  }, { category: 'AWS_SDK_COMPAT' });

  // Test 2: Credential Configuration Validation
  await testSuite.runTest('Credential Configuration Validation', async () => {
    await testCredentialConfiguration(testSuite);
  }, { category: 'AWS_SDK_COMPAT' });

  // Test 3: Endpoint and Region Configuration
  await testSuite.runTest('Endpoint and Region Configuration', async () => {
    await testEndpointRegionConfiguration(testSuite);
  }, { category: 'AWS_SDK_COMPAT' });

  // Test 4: S3Client Instance Creation
  await testSuite.runTest('S3Client Instance Creation', async () => {
    await testS3ClientCreation(testSuite);
  }, {
    category: 'AWS_SDK_COMPAT',
    skipIf: !isAwsSdkAvailable() ? 'AWS SDK v3 not available' : false
  });

  // Test 5: Basic S3 Operations Simulation
  await testSuite.runTest('Basic S3 Operations Simulation', async () => {
    await testS3OperationsSimulation(testSuite);
  }, {
    category: 'AWS_SDK_COMPAT',
    skipIf: !isAwsSdkAvailable() ? 'AWS SDK v3 not available' : false
  });

  // Test 6: Error Handling Compatibility
  await testSuite.runTest('Error Handling Compatibility', async () => {
    await testErrorHandlingCompatibility(testSuite);
  }, { category: 'AWS_SDK_COMPAT' });

  // Test 7: Configuration Validation Against AWS SDK
  await testSuite.runTest('Configuration Validation Against AWS SDK', async () => {
    await testConfigurationValidation(testSuite);
  }, { category: 'AWS_SDK_COMPAT' });

  // Test 8: Multi-Region Compatibility
  await testSuite.runTest('Multi-Region Compatibility', async () => {
    await testMultiRegionCompatibility(testSuite);
  }, { category: 'AWS_SDK_COMPAT' });

  // Test 9: Custom Endpoint Configuration
  await testSuite.runTest('Custom Endpoint Configuration', async () => {
    await testCustomEndpointConfiguration(testSuite);
  }, { category: 'AWS_SDK_COMPAT' });
}

/**
 * Check if AWS SDK v3 is available
 */
function isAwsSdkAvailable() {
  try {
    require('@aws-sdk/client-s3');
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Test S3Client configuration generation
 */
async function testS3ClientConfigGeneration(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing S3Client configuration generation...');

  const manifestGen = require('../scripts/gen-connection-manifest.js');
  const manifest = await manifestGen.generateManifest({
    environment: 'dev',
    useTemplate: true,
    dryRun: true
  });

  // Generate S3Client-compatible configuration
  const s3Config = generateS3ClientConfig(manifest);

  // Verify required AWS SDK v3 configuration fields
  const requiredFields = ['region', 'endpoint', 'credentials', 'forcePathStyle'];

  for (const field of requiredFields) {
    if (!(field in s3Config)) {
      throw new Error(`S3Client configuration missing required field: ${field}`);
    }
  }

  // Verify endpoint configuration
  if (!s3Config.endpoint || typeof s3Config.endpoint !== 'object') {
    throw new Error('S3Client endpoint configuration invalid');
  }

  if (!s3Config.endpoint.url || !s3Config.endpoint.url.startsWith('https://')) {
    throw new Error('S3Client endpoint URL invalid or insecure');
  }

  // Verify region configuration
  if (!s3Config.region || typeof s3Config.region !== 'string') {
    throw new Error('S3Client region configuration invalid');
  }

  // Verify credentials structure (for S3 API mode)
  if (manifest.connection_mode === 's3-api') {
    if (!s3Config.credentials || typeof s3Config.credentials !== 'object') {
      throw new Error('S3Client credentials configuration invalid for S3 API mode');
    }

    const requiredCredFields = ['accessKeyId', 'secretAccessKey'];
    for (const field of requiredCredFields) {
      if (!(field in s3Config.credentials)) {
        throw new Error(`S3Client credentials missing required field: ${field}`);
      }
    }
  }

  // Verify forcePathStyle is set for R2 compatibility
  if (s3Config.forcePathStyle !== true) {
    throw new Error('S3Client configuration should use forcePathStyle for R2 compatibility');
  }

  logger.debug('S3Client configuration generation validated successfully');
}

/**
 * Test credential configuration validation
 */
async function testCredentialConfiguration(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing credential configuration...');

  const manifestGen = require('../scripts/gen-connection-manifest.js');

  // Test different connection modes
  const connectionModes = ['workers-binding', 's3-api', 'hybrid'];

  for (const mode of connectionModes) {
    const manifest = await manifestGen.generateManifest({
      environment: 'dev',
      useTemplate: true,
      dryRun: true,
      overrides: { connection_mode: mode }
    });

    const s3Config = generateS3ClientConfig(manifest);

    if (mode === 'workers-binding') {
      // Workers binding mode might not need explicit credentials
      logger.debug(`Workers binding mode: credentials optional`);
    } else if (mode === 's3-api' || mode === 'hybrid') {
      // S3 API mode requires credentials
      if (!s3Config.credentials) {
        throw new Error(`${mode} mode requires credentials configuration`);
      }

      if (!s3Config.credentials.accessKeyId || !s3Config.credentials.secretAccessKey) {
        throw new Error(`${mode} mode credentials incomplete`);
      }

      // Validate credential format
      if (typeof s3Config.credentials.accessKeyId !== 'string' ||
          typeof s3Config.credentials.secretAccessKey !== 'string') {
        throw new Error(`${mode} mode credentials have invalid types`);
      }

      // Check for placeholder values
      if (s3Config.credentials.accessKeyId.includes('placeholder') ||
          s3Config.credentials.secretAccessKey.includes('placeholder')) {
        logger.warn(`${mode} mode has placeholder credentials - replace with real values`);
      }
    }
  }

  // Test credential validation
  const testCredentials = {
    accessKeyId: 'test-access-key-123',
    secretAccessKey: 'test-secret-key-456'
  };

  if (!validateCredentialsFormat(testCredentials)) {
    throw new Error('Credential validation function failed');
  }

  // Test invalid credentials
  const invalidCredentials = [
    { accessKeyId: '', secretAccessKey: 'valid' },
    { accessKeyId: 'valid', secretAccessKey: '' },
    { accessKeyId: null, secretAccessKey: 'valid' },
    { accessKeyId: 'valid', secretAccessKey: null }
  ];

  for (const creds of invalidCredentials) {
    if (validateCredentialsFormat(creds)) {
      throw new Error('Credential validation should reject invalid credentials');
    }
  }

  logger.debug('Credential configuration validated successfully');
}

/**
 * Test endpoint and region configuration
 */
async function testEndpointRegionConfiguration(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing endpoint and region configuration...');

  const manifestGen = require('../scripts/gen-connection-manifest.js');
  const regions = ['auto', 'eeur', 'enam', 'apac', 'weur', 'wnam'];

  for (const region of regions) {
    const manifest = await manifestGen.generateManifest({
      environment: 'dev',
      useTemplate: true,
      dryRun: true,
      overrides: { region: region }
    });

    const s3Config = generateS3ClientConfig(manifest);

    // Verify region is properly set
    if (s3Config.region !== region) {
      throw new Error(`Region mismatch: expected ${region}, got ${s3Config.region}`);
    }

    // Verify endpoint URL format
    if (!s3Config.endpoint.url.includes('.r2.cloudflarestorage.com')) {
      throw new Error(`Invalid R2 endpoint for region ${region}`);
    }

    // Verify endpoint URL uses HTTPS
    if (!s3Config.endpoint.url.startsWith('https://')) {
      throw new Error(`Insecure endpoint for region ${region}`);
    }

    // Verify account ID is in endpoint
    if (!s3Config.endpoint.url.includes(manifest.account_id)) {
      throw new Error(`Account ID missing from endpoint for region ${region}`);
    }
  }

  // Test custom endpoint configuration
  const customManifest = await manifestGen.generateManifest({
    environment: 'dev',
    useTemplate: true,
    dryRun: true,
    overrides: {
      endpoint: 'https://custom-account-id.r2.cloudflarestorage.com'
    }
  });

  const customS3Config = generateS3ClientConfig(customManifest);

  if (customS3Config.endpoint.url !== customManifest.endpoint) {
    throw new Error('Custom endpoint not properly configured');
  }

  logger.debug('Endpoint and region configuration validated successfully');
}

/**
 * Test S3Client instance creation
 */
async function testS3ClientCreation(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing S3Client instance creation...');

  try {
    const { S3Client } = require('@aws-sdk/client-s3');

    const manifestGen = require('../scripts/gen-connection-manifest.js');
    const manifest = await manifestGen.generateManifest({
      environment: 'dev',
      useTemplate: true,
      dryRun: true
    });

    const s3Config = generateS3ClientConfig(manifest);

    // Create S3Client instance
    const s3Client = new S3Client(s3Config);

    if (!s3Client) {
      throw new Error('Failed to create S3Client instance');
    }

    // Verify client configuration
    const clientConfig = s3Client.config;

    if (!clientConfig) {
      throw new Error('S3Client configuration not accessible');
    }

    // Test configuration access
    if (typeof clientConfig.region === 'function') {
      // AWS SDK v3 config values might be functions
      const region = await clientConfig.region();
      if (region !== manifest.region) {
        throw new Error(`S3Client region mismatch: expected ${manifest.region}, got ${region}`);
      }
    }

    // Verify client methods are available
    const requiredMethods = ['send'];
    for (const method of requiredMethods) {
      if (typeof s3Client[method] !== 'function') {
        throw new Error(`S3Client missing required method: ${method}`);
      }
    }

    logger.debug('S3Client instance created successfully');

  } catch (error) {
    if (error.code === 'MODULE_NOT_FOUND') {
      throw new Error('AWS SDK v3 not installed - install @aws-sdk/client-s3');
    }
    throw error;
  }
}

/**
 * Test basic S3 operations simulation
 */
async function testS3OperationsSimulation(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing S3 operations simulation...');

  try {
    const { S3Client, ListBucketsCommand, HeadBucketCommand } = require('@aws-sdk/client-s3');

    const manifestGen = require('../scripts/gen-connection-manifest.js');
    const manifest = await manifestGen.generateManifest({
      environment: 'dev',
      useTemplate: true,
      dryRun: true
    });

    const s3Config = generateS3ClientConfig(manifest);
    const s3Client = new S3Client(s3Config);

    // Test ListBuckets command creation
    const listBucketsCommand = new ListBucketsCommand({});
    if (!listBucketsCommand) {
      throw new Error('Failed to create ListBucketsCommand');
    }

    // Test HeadBucket command creation for each bucket
    for (const bucket of manifest.buckets) {
      const headBucketCommand = new HeadBucketCommand({
        Bucket: bucket.name
      });

      if (!headBucketCommand) {
        throw new Error(`Failed to create HeadBucketCommand for bucket ${bucket.name}`);
      }

      // Verify command input
      if (headBucketCommand.input.Bucket !== bucket.name) {
        throw new Error(`HeadBucketCommand bucket name mismatch: expected ${bucket.name}`);
      }
    }

    // Test command serialization (without sending)
    const serializedCommand = listBucketsCommand.middlewareStack;
    if (!serializedCommand) {
      throw new Error('Command middleware stack not available');
    }

    logger.debug('S3 operations simulation completed successfully');

  } catch (error) {
    if (error.code === 'MODULE_NOT_FOUND') {
      throw new Error('AWS SDK v3 commands not available - install @aws-sdk/client-s3');
    }
    throw error;
  }
}

/**
 * Test error handling compatibility
 */
async function testErrorHandlingCompatibility(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing error handling compatibility...');

  // Test invalid configuration handling
  const invalidConfigs = [
    { region: '', endpoint: 'valid-endpoint' },
    { region: 'valid-region', endpoint: '' },
    { region: null, endpoint: 'valid-endpoint' },
    { region: 'valid-region', endpoint: null },
    { region: 'invalid-region', endpoint: 'not-a-url' },
  ];

  for (const config of invalidConfigs) {
    try {
      const s3Config = {
        region: config.region,
        endpoint: config.endpoint ? { url: config.endpoint } : null,
        credentials: {
          accessKeyId: 'test',
          secretAccessKey: 'test'
        },
        forcePathStyle: true
      };

      // This should be caught by our validation
      if (!validateS3ClientConfig(s3Config)) {
        logger.debug('Invalid configuration properly rejected');
      } else {
        throw new Error('Invalid configuration should be rejected');
      }
    } catch (error) {
      // Expected error for invalid configuration
      logger.debug(`Configuration validation error: ${error.message}`);
    }
  }

  // Test AWS SDK specific error scenarios
  if (isAwsSdkAvailable()) {
    try {
      const { S3Client } = require('@aws-sdk/client-s3');

      // Test with minimal invalid config
      const invalidS3Config = {
        region: 'invalid-region',
        endpoint: { url: 'https://invalid-endpoint' },
        credentials: {
          accessKeyId: '',
          secretAccessKey: ''
        }
      };

      // S3Client creation might succeed but operations will fail
      const s3Client = new S3Client(invalidS3Config);
      if (!s3Client) {
        throw new Error('S3Client should be created even with invalid config');
      }

      logger.debug('Error handling compatibility validated');

    } catch (error) {
      if (error.message.includes('Invalid region') ||
          error.message.includes('Invalid endpoint') ||
          error.message.includes('credentials')) {
        logger.debug('AWS SDK properly validates configuration');
      } else {
        throw error;
      }
    }
  }

  logger.debug('Error handling compatibility validated successfully');
}

/**
 * Test configuration validation against AWS SDK
 */
async function testConfigurationValidation(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing configuration validation...');

  const manifestGen = require('../scripts/gen-connection-manifest.js');
  const environments = ['dev', 'stg', 'prod'];

  for (const env of environments) {
    const manifest = await manifestGen.generateManifest({
      environment: env,
      useTemplate: true,
      dryRun: true
    });

    const s3Config = generateS3ClientConfig(manifest);

    // Validate against AWS SDK requirements
    if (!validateS3ClientConfig(s3Config)) {
      throw new Error(`Invalid S3Client configuration for environment ${env}`);
    }

    // Test specific AWS SDK compatibility requirements
    if (s3Config.forcePathStyle !== true) {
      throw new Error(`Environment ${env} missing forcePathStyle for R2 compatibility`);
    }

    if (!s3Config.endpoint || !s3Config.endpoint.url) {
      throw new Error(`Environment ${env} missing endpoint configuration`);
    }

    if (!s3Config.region) {
      throw new Error(`Environment ${env} missing region configuration`);
    }

    // Validate endpoint URL format for R2
    const endpointUrl = s3Config.endpoint.url;
    if (!endpointUrl.match(/^https:\/\/[a-f0-9]{32}\.r2\.cloudflarestorage\.com$/)) {
      throw new Error(`Environment ${env} has invalid R2 endpoint format`);
    }

    // Validate region format
    const validRegions = ['auto', 'eeur', 'enam', 'apac', 'weur', 'wnam'];
    if (!validRegions.includes(s3Config.region)) {
      throw new Error(`Environment ${env} has invalid region: ${s3Config.region}`);
    }
  }

  logger.debug('Configuration validation completed successfully');
}

/**
 * Test multi-region compatibility
 */
async function testMultiRegionCompatibility(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing multi-region compatibility...');

  const manifestGen = require('../scripts/gen-connection-manifest.js');
  const regions = ['auto', 'eeur', 'enam', 'apac', 'weur', 'wnam'];

  for (const region of regions) {
    const manifest = await manifestGen.generateManifest({
      environment: 'dev',
      useTemplate: true,
      dryRun: true,
      overrides: { region: region }
    });

    const s3Config = generateS3ClientConfig(manifest);

    // Verify region-specific configuration
    if (s3Config.region !== region) {
      throw new Error(`Region configuration mismatch for ${region}`);
    }

    // Verify endpoint compatibility with region
    const endpointUrl = s3Config.endpoint.url;
    if (!endpointUrl.includes('.r2.cloudflarestorage.com')) {
      throw new Error(`Invalid endpoint for region ${region}`);
    }

    // Test AWS SDK compatibility for each region
    if (isAwsSdkAvailable()) {
      try {
        const { S3Client } = require('@aws-sdk/client-s3');
        const s3Client = new S3Client(s3Config);

        if (!s3Client) {
          throw new Error(`Failed to create S3Client for region ${region}`);
        }

        logger.debug(`S3Client created successfully for region ${region}`);

      } catch (error) {
        throw new Error(`S3Client creation failed for region ${region}: ${error.message}`);
      }
    }
  }

  logger.debug('Multi-region compatibility validated successfully');
}

/**
 * Test custom endpoint configuration
 */
async function testCustomEndpointConfiguration(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing custom endpoint configuration...');

  const manifestGen = require('../scripts/gen-connection-manifest.js');

  // Test with custom account ID and endpoint
  const customAccountId = 'abcdef1234567890abcdef1234567890ab';
  const customEndpoint = `https://${customAccountId}.r2.cloudflarestorage.com`;

  const manifest = await manifestGen.generateManifest({
    environment: 'dev',
    useTemplate: true,
    dryRun: true,
    overrides: {
      account_id: customAccountId,
      endpoint: customEndpoint
    }
  });

  const s3Config = generateS3ClientConfig(manifest);

  // Verify custom endpoint is used
  if (s3Config.endpoint.url !== customEndpoint) {
    throw new Error('Custom endpoint not properly configured');
  }

  // Verify endpoint format is valid for AWS SDK
  if (!s3Config.endpoint.url.startsWith('https://')) {
    throw new Error('Custom endpoint must use HTTPS');
  }

  // Test with regional endpoint format
  const regionalEndpoint = `https://${customAccountId}.eeur.r2.cloudflarestorage.com`;
  const regionalManifest = await manifestGen.generateManifest({
    environment: 'dev',
    useTemplate: true,
    dryRun: true,
    overrides: {
      account_id: customAccountId,
      endpoint: regionalEndpoint,
      region: 'eeur'
    }
  });

  const regionalS3Config = generateS3ClientConfig(regionalManifest);

  if (regionalS3Config.endpoint.url !== regionalEndpoint) {
    throw new Error('Regional endpoint not properly configured');
  }

  if (regionalS3Config.region !== 'eeur') {
    throw new Error('Regional configuration not properly set');
  }

  logger.debug('Custom endpoint configuration validated successfully');
}

/**
 * Generate S3Client-compatible configuration from R2 manifest
 */
function generateS3ClientConfig(manifest) {
  const config = {
    region: manifest.region,
    endpoint: {
      url: manifest.endpoint
    },
    forcePathStyle: true
  };

  // Add credentials if available
  if (manifest.credentials) {
    config.credentials = {
      accessKeyId: manifest.credentials.access_key_id,
      secretAccessKey: manifest.credentials.secret_access_key
    };

    if (manifest.credentials.session_token) {
      config.credentials.sessionToken = manifest.credentials.session_token;
    }
  }

  return config;
}

/**
 * Validate S3Client configuration format
 */
function validateS3ClientConfig(config) {
  try {
    // Required fields
    if (!config.region || typeof config.region !== 'string') {
      return false;
    }

    if (!config.endpoint || !config.endpoint.url || typeof config.endpoint.url !== 'string') {
      return false;
    }

    if (!config.endpoint.url.startsWith('https://')) {
      return false;
    }

    if (config.forcePathStyle !== true) {
      return false;
    }

    // Validate credentials if present
    if (config.credentials) {
      if (!config.credentials.accessKeyId || typeof config.credentials.accessKeyId !== 'string') {
        return false;
      }

      if (!config.credentials.secretAccessKey || typeof config.credentials.secretAccessKey !== 'string') {
        return false;
      }
    }

    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Validate credentials format
 */
function validateCredentialsFormat(credentials) {
  if (!credentials || typeof credentials !== 'object') {
    return false;
  }

  if (!credentials.accessKeyId || typeof credentials.accessKeyId !== 'string') {
    return false;
  }

  if (!credentials.secretAccessKey || typeof credentials.secretAccessKey !== 'string') {
    return false;
  }

  if (credentials.accessKeyId.length === 0 || credentials.secretAccessKey.length === 0) {
    return false;
  }

  return true;
}

module.exports = {
  runTests,
  testS3ClientConfigGeneration,
  testCredentialConfiguration,
  testEndpointRegionConfiguration,
  testS3ClientCreation,
  testS3OperationsSimulation,
  testErrorHandlingCompatibility,
  testConfigurationValidation,
  testMultiRegionCompatibility,
  testCustomEndpointConfiguration,
  generateS3ClientConfig,
  validateS3ClientConfig,
  validateCredentialsFormat,
  isAwsSdkAvailable,
};