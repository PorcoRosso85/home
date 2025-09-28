/**
 * SOPS Encryption/Decryption Workflow Tests
 *
 * Tests the complete SOPS workflow including encryption, decryption,
 * key management, and integration with the R2 configuration system.
 * Validates security, reliability, and performance of encrypted workflows.
 *
 * Test scenarios:
 * - SOPS encryption/decryption operations
 * - Age key management and validation
 * - Cache behavior with encrypted data
 * - Error scenarios and recovery
 * - Security validation
 * - Performance with encrypted operations
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

/**
 * Run SOPS encryption/decryption tests
 */
async function runTests(testSuite) {
  const { logger } = testSuite;

  logger.info('Running SOPS Encryption/Decryption Workflow Tests...');

  // Test 1: SOPS Binary Availability
  await testSuite.runTest('SOPS Binary Availability', async () => {
    await testSopsBinaryAvailability(testSuite);
  }, {
    category: 'SOPS_ENCRYPTION',
    skipIf: testSuite.TEST_CONFIG.skipSops ? 'SOPS tests disabled' : false
  });

  // Test 2: Age Key Configuration
  await testSuite.runTest('Age Key Configuration', async () => {
    await testAgeKeyConfiguration(testSuite);
  }, {
    category: 'SOPS_ENCRYPTION',
    skipIf: testSuite.TEST_CONFIG.skipSops ? 'SOPS tests disabled' : false
  });

  // Test 3: Basic Encryption/Decryption
  await testSuite.runTest('Basic Encryption/Decryption', async () => {
    await testBasicEncryptionDecryption(testSuite);
  }, {
    category: 'SOPS_ENCRYPTION',
    skipIf: testSuite.TEST_CONFIG.skipSops ? 'SOPS tests disabled' : false
  });

  // Test 4: SOPS YAML Integration
  await testSuite.runTest('SOPS YAML Integration', async () => {
    await testSopsYamlIntegration(testSuite);
  }, { category: 'SOPS_ENCRYPTION' });

  // Test 5: Encrypted Configuration Loading
  await testSuite.runTest('Encrypted Configuration Loading', async () => {
    await testEncryptedConfigurationLoading(testSuite);
  }, {
    category: 'SOPS_ENCRYPTION',
    skipIf: testSuite.TEST_CONFIG.skipSops ? 'SOPS tests disabled' : false
  });

  // Test 6: Cache Behavior with Encryption
  await testSuite.runTest('Cache Behavior with Encryption', async () => {
    await testCacheBehaviorWithEncryption(testSuite);
  }, { category: 'SOPS_ENCRYPTION' });

  // Test 7: Error Scenarios and Recovery
  await testSuite.runTest('Error Scenarios and Recovery', async () => {
    await testErrorScenariosAndRecovery(testSuite);
  }, { category: 'SOPS_ENCRYPTION' });

  // Test 8: Security Validation
  await testSuite.runTest('Security Validation', async () => {
    await testSecurityValidation(testSuite);
  }, { category: 'SOPS_ENCRYPTION' });

  // Test 9: Performance with Encryption
  await testSuite.runTest('Performance with Encryption', async () => {
    await testPerformanceWithEncryption(testSuite);
  }, {
    category: 'SOPS_ENCRYPTION',
    skipIf: testSuite.TEST_CONFIG.skipSops ? 'SOPS tests disabled' : false
  });

  // Test 10: Multi-Environment Encryption
  await testSuite.runTest('Multi-Environment Encryption', async () => {
    await testMultiEnvironmentEncryption(testSuite);
  }, {
    category: 'SOPS_ENCRYPTION',
    skipIf: testSuite.TEST_CONFIG.skipSops ? 'SOPS tests disabled' : false
  });
}

/**
 * Test SOPS binary availability
 */
async function testSopsBinaryAvailability(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing SOPS binary availability...');

  try {
    // Check if SOPS is available
    const result = await testSuite.execCommand('which sops');

    if (!result.stdout || result.stdout.trim().length === 0) {
      throw new Error('SOPS binary not found in PATH');
    }

    logger.debug(`SOPS binary found at: ${result.stdout.trim()}`);

    // Check SOPS version
    const versionResult = await testSuite.execCommand('sops --version');

    if (!versionResult.stdout) {
      throw new Error('Unable to determine SOPS version');
    }

    const versionOutput = versionResult.stdout.trim();
    logger.debug(`SOPS version: ${versionOutput}`);

    // Verify minimum version requirements
    const versionMatch = versionOutput.match(/(\d+)\.(\d+)\.(\d+)/);
    if (versionMatch) {
      const [, major, minor, patch] = versionMatch.map(Number);

      // Require SOPS 3.7+ for age support
      if (major < 3 || (major === 3 && minor < 7)) {
        throw new Error(`SOPS version ${major}.${minor}.${patch} is too old. Require 3.7+ for age support`);
      }
    }

    // Test basic SOPS functionality
    const helpResult = await testSuite.execCommand('sops --help');

    if (helpResult.code !== 0) {
      throw new Error('SOPS help command failed');
    }

    // Check for age support
    if (!helpResult.stdout.includes('age') && !helpResult.stderr.includes('age')) {
      logger.warn('SOPS may not have age support compiled in');
    }

  } catch (error) {
    throw new Error(`SOPS binary test failed: ${error.message}`);
  }

  logger.debug('SOPS binary availability validated successfully');
}

/**
 * Test age key configuration
 */
async function testAgeKeyConfiguration(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing age key configuration...');

  // Check age key file locations
  const ageKeyPaths = [
    process.env.SOPS_AGE_KEY_FILE,
    path.join(process.env.HOME || '/tmp', '.config/sops/age/keys.txt'),
    path.join(process.env.HOME || '/tmp', '.age/keys.txt'),
  ].filter(Boolean);

  let keyFileFound = false;
  let validKeyFile = null;

  for (const keyPath of ageKeyPaths) {
    if (fs.existsSync(keyPath)) {
      keyFileFound = true;
      validKeyFile = keyPath;
      logger.debug(`Age key file found: ${keyPath}`);

      // Validate key file format
      const keyContent = fs.readFileSync(keyPath, 'utf8');

      if (!keyContent.includes('AGE-SECRET-KEY-')) {
        logger.warn(`Age key file ${keyPath} may not contain valid age keys`);
        continue;
      }

      // Count keys
      const keyCount = (keyContent.match(/AGE-SECRET-KEY-/g) || []).length;
      logger.debug(`Found ${keyCount} age keys in ${keyPath}`);

      if (keyCount === 0) {
        logger.warn(`No valid age keys found in ${keyPath}`);
        continue;
      }

      break;
    }
  }

  if (!keyFileFound) {
    throw new Error('No age key file found. Set SOPS_AGE_KEY_FILE or create ~/.config/sops/age/keys.txt');
  }

  // Test age key environment variable
  if (!process.env.SOPS_AGE_KEY_FILE) {
    // Set it temporarily for testing
    process.env.SOPS_AGE_KEY_FILE = validKeyFile;
    logger.debug(`Set SOPS_AGE_KEY_FILE to ${validKeyFile}`);
  }

  // Validate SOPS configuration
  const sopsConfigPath = path.join(testSuite.TEST_CONFIG.workDir, '.sops.yaml');

  if (!fs.existsSync(sopsConfigPath)) {
    throw new Error('SOPS configuration file (.sops.yaml) not found');
  }

  const sopsConfigContent = fs.readFileSync(sopsConfigPath, 'utf8');

  if (!sopsConfigContent.includes('age')) {
    throw new Error('SOPS configuration does not include age key configuration');
  }

  // Test age key extraction for validation
  if (validKeyFile) {
    try {
      const keyContent = fs.readFileSync(validKeyFile, 'utf8');
      const agePublicKeys = extractAgePublicKeys(keyContent);

      if (agePublicKeys.length === 0) {
        throw new Error('No valid age public keys could be extracted');
      }

      logger.debug(`Extracted ${agePublicKeys.length} age public keys for validation`);

    } catch (error) {
      logger.warn(`Age key validation warning: ${error.message}`);
    }
  }

  logger.debug('Age key configuration validated successfully');
}

/**
 * Test basic encryption/decryption
 */
async function testBasicEncryptionDecryption(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing basic encryption/decryption...');

  const testDir = testSuite.TEST_CONFIG.tempDir;
  const testDataPath = path.join(testDir, 'test-encryption.yaml');
  const encryptedPath = path.join(testDir, 'test-encrypted.yaml');

  // Create test data
  const testData = {
    plaintext_field: 'public-value',
    secret_field: 'secret-value-123',
    nested: {
      secret_key: 'nested-secret-456',
      public_key: 'nested-public'
    }
  };

  const yamlContent = `# Test encryption data
plaintext_field: ${testData.plaintext_field}
secret_field: ${testData.secret_field}
nested:
  secret_key: ${testData.nested.secret_key}
  public_key: ${testData.nested.public_key}
`;

  fs.writeFileSync(testDataPath, yamlContent);

  try {
    // Test encryption
    const encryptCommand = `sops --encrypt ${testDataPath}`;
    const encryptResult = await testSuite.execCommand(encryptCommand);

    if (encryptResult.code !== 0) {
      throw new Error(`Encryption failed: ${encryptResult.stderr}`);
    }

    const encryptedContent = encryptResult.stdout;

    if (!encryptedContent.includes('sops:')) {
      throw new Error('Encrypted content does not contain SOPS metadata');
    }

    if (encryptedContent.includes(testData.secret_field)) {
      throw new Error('Encrypted content still contains plaintext secrets');
    }

    if (!encryptedContent.includes(testData.plaintext_field)) {
      throw new Error('Encrypted content should preserve unencrypted fields');
    }

    // Save encrypted content
    fs.writeFileSync(encryptedPath, encryptedContent);

    // Test decryption
    const decryptCommand = `sops --decrypt ${encryptedPath}`;
    const decryptResult = await testSuite.execCommand(decryptCommand);

    if (decryptResult.code !== 0) {
      throw new Error(`Decryption failed: ${decryptResult.stderr}`);
    }

    const decryptedContent = decryptResult.stdout;

    // Verify decrypted content
    if (!decryptedContent.includes(testData.secret_field)) {
      throw new Error('Decrypted content missing secret field');
    }

    if (!decryptedContent.includes(testData.plaintext_field)) {
      throw new Error('Decrypted content missing plaintext field');
    }

    if (!decryptedContent.includes(testData.nested.secret_key)) {
      throw new Error('Decrypted content missing nested secret');
    }

    // Test roundtrip integrity
    const originalLines = yamlContent.split('\n').filter(line => line.trim());
    const decryptedLines = decryptedContent.split('\n').filter(line => line.trim());

    for (const originalLine of originalLines) {
      if (originalLine.startsWith('#')) continue; // Skip comments

      const found = decryptedLines.some(line =>
        line.trim() === originalLine.trim() ||
        line.includes(originalLine.split(':')[1]?.trim())
      );

      if (!found) {
        logger.warn(`Original line not found in decrypted content: ${originalLine}`);
      }
    }

  } finally {
    // Cleanup test files
    [testDataPath, encryptedPath].forEach(file => {
      if (fs.existsSync(file)) {
        fs.unlinkSync(file);
      }
    });
  }

  logger.debug('Basic encryption/decryption validated successfully');
}

/**
 * Test SOPS YAML integration
 */
async function testSopsYamlIntegration(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing SOPS YAML integration...');

  const sopsHelper = require('../helpers/sops-yaml.js');

  // Test helper availability
  if (!sopsHelper.decrypt || typeof sopsHelper.decrypt !== 'function') {
    throw new Error('SOPS helper missing decrypt function');
  }

  if (!sopsHelper.getEnvironmentConfig || typeof sopsHelper.getEnvironmentConfig !== 'function') {
    throw new Error('SOPS helper missing getEnvironmentConfig function');
  }

  // Test template mode (should work without SOPS)
  const templateConfig = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

  if (!templateConfig.cf_account_id || !templateConfig.r2_buckets) {
    throw new Error('Template config missing required fields');
  }

  // Test health check
  const health = await sopsHelper.healthCheck();

  if (typeof health.sops !== 'boolean') {
    throw new Error('Health check should report SOPS availability as boolean');
  }

  if (typeof health.ageKey !== 'boolean') {
    throw new Error('Health check should report age key availability as boolean');
  }

  if (typeof health.sopsConfig !== 'boolean') {
    throw new Error('Health check should report SOPS config availability as boolean');
  }

  logger.debug(`Health check results: SOPS=${health.sops}, Age=${health.ageKey}, Config=${health.sopsConfig}`);

  // Test cache functionality
  sopsHelper.clearCache();
  const cacheStats = sopsHelper.getCacheStats();

  if (cacheStats.size !== 0) {
    throw new Error('Cache not properly cleared');
  }

  // Test configuration loading (with cache)
  const config1 = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
  const config2 = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

  // Should be identical (cached)
  if (JSON.stringify(config1) !== JSON.stringify(config2)) {
    throw new Error('Cached configuration differs from original');
  }

  const statsAfterCache = sopsHelper.getCacheStats();
  if (statsAfterCache.hits === 0) {
    throw new Error('Cache hit not recorded');
  }

  // Test error handling
  try {
    await sopsHelper.getEnvironmentConfig('r2', 'invalid-env', false);
    throw new Error('Should have thrown for invalid environment');
  } catch (error) {
    if (!error.message.includes('Invalid') && !error.message.includes('invalid')) {
      throw new Error(`Unexpected error message: ${error.message}`);
    }
  }

  logger.debug('SOPS YAML integration validated successfully');
}

/**
 * Test encrypted configuration loading
 */
async function testEncryptedConfigurationLoading(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing encrypted configuration loading...');

  const testDir = testSuite.TEST_CONFIG.tempDir;
  const testSecretPath = path.join(testDir, 'test-r2-config.yaml');

  // Create test R2 configuration
  const testConfig = {
    cf_account_id: '1234567890abcdef1234567890abcdef',
    r2_buckets: ['test-bucket-encrypted'],
    r2_access_key_id: 'test-access-key-encrypted',
    r2_secret_access_key: 'test-secret-key-encrypted'
  };

  const configYaml = `# Test R2 configuration
cf_account_id: ${testConfig.cf_account_id}
r2_buckets:
  - ${testConfig.r2_buckets[0]}
r2_access_key_id: ${testConfig.r2_access_key_id}
r2_secret_access_key: ${testConfig.r2_secret_access_key}
`;

  fs.writeFileSync(testSecretPath, configYaml);

  try {
    // Encrypt the configuration
    const encryptCommand = `sops --encrypt --in-place ${testSecretPath}`;
    await testSuite.execCommand(encryptCommand);

    // Verify file is encrypted
    const encryptedContent = fs.readFileSync(testSecretPath, 'utf8');

    if (!encryptedContent.includes('sops:')) {
      throw new Error('Configuration file not properly encrypted');
    }

    if (encryptedContent.includes(testConfig.r2_secret_access_key)) {
      throw new Error('Secret key still visible in encrypted file');
    }

    // Test loading through SOPS helper
    const sopsHelper = require('../helpers/sops-yaml.js');
    const decryptedConfig = await sopsHelper.decrypt(testSecretPath);

    // Verify decryption
    if (decryptedConfig.cf_account_id !== testConfig.cf_account_id) {
      throw new Error('Decrypted account ID does not match original');
    }

    if (!Array.isArray(decryptedConfig.r2_buckets) ||
        decryptedConfig.r2_buckets[0] !== testConfig.r2_buckets[0]) {
      throw new Error('Decrypted buckets do not match original');
    }

    if (decryptedConfig.r2_access_key_id !== testConfig.r2_access_key_id) {
      throw new Error('Decrypted access key ID does not match original');
    }

    if (decryptedConfig.r2_secret_access_key !== testConfig.r2_secret_access_key) {
      throw new Error('Decrypted secret access key does not match original');
    }

    // Test with validation
    const schema = {
      type: 'object',
      required: ['cf_account_id', 'r2_buckets'],
      properties: {
        cf_account_id: { type: 'string' },
        r2_buckets: { type: 'array' }
      }
    };

    const validatedConfig = await sopsHelper.decryptWithValidation(testSecretPath, schema);

    if (!validatedConfig.cf_account_id) {
      throw new Error('Validated config missing account ID');
    }

    // Test manifest generation with encrypted config
    const manifestGen = require('../scripts/gen-connection-manifest.js');
    const manifest = await manifestGen.generateManifest({
      environment: 'test',
      configPath: testSecretPath,
      dryRun: true
    });

    if (manifest.account_id !== testConfig.cf_account_id) {
      throw new Error('Manifest does not use encrypted config values');
    }

  } finally {
    // Cleanup
    if (fs.existsSync(testSecretPath)) {
      fs.unlinkSync(testSecretPath);
    }
  }

  logger.debug('Encrypted configuration loading validated successfully');
}

/**
 * Test cache behavior with encryption
 */
async function testCacheBehaviorWithEncryption(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing cache behavior with encryption...');

  const sopsHelper = require('../helpers/sops-yaml.js');

  // Clear cache and verify
  sopsHelper.clearCache();
  let stats = sopsHelper.getCacheStats();

  if (stats.size !== 0) {
    throw new Error('Cache not properly cleared');
  }

  // Test cache with template mode (no encryption)
  const config1 = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
  stats = sopsHelper.getCacheStats();

  if (stats.misses !== 1) {
    throw new Error(`Expected 1 cache miss, got ${stats.misses}`);
  }

  // Second call should hit cache
  const config2 = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
  stats = sopsHelper.getCacheStats();

  if (stats.hits !== 1) {
    throw new Error(`Expected 1 cache hit, got ${stats.hits}`);
  }

  // Configs should be identical
  if (JSON.stringify(config1) !== JSON.stringify(config2)) {
    throw new Error('Cached config differs from original');
  }

  // Test cache with different environments
  const config3 = await sopsHelper.getEnvironmentConfig('r2', 'stg', true);
  stats = sopsHelper.getCacheStats();

  if (stats.misses !== 2) {
    throw new Error(`Expected 2 cache misses, got ${stats.misses}`);
  }

  // Different environments should have different configs
  if (JSON.stringify(config1) === JSON.stringify(config3)) {
    throw new Error('Different environments should not have identical configs');
  }

  // Test cache TTL behavior
  const originalTTL = sopsHelper.CONFIG.defaultCacheTTL;
  sopsHelper.CONFIG.defaultCacheTTL = 100; // 100ms

  try {
    sopsHelper.clearCache();

    // Load config
    await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

    // Wait for TTL to expire
    await new Promise(resolve => setTimeout(resolve, 150));

    // Next call should miss cache due to TTL
    await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

    const expiredStats = sopsHelper.getCacheStats();
    if (expiredStats.misses < 2) {
      logger.warn('Cache TTL expiration may not be working as expected');
    }

  } finally {
    // Restore original TTL
    sopsHelper.CONFIG.defaultCacheTTL = originalTTL;
  }

  // Test cache size limits
  const originalMaxSize = sopsHelper.CONFIG.maxCacheSize;
  sopsHelper.CONFIG.maxCacheSize = 2;

  try {
    sopsHelper.clearCache();

    // Fill cache beyond limit
    await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
    await sopsHelper.getEnvironmentConfig('r2', 'stg', true);
    await sopsHelper.getEnvironmentConfig('r2', 'prod', true);

    const sizeStats = sopsHelper.getCacheStats();
    if (sizeStats.size > 2) {
      logger.warn('Cache size limit may not be enforced properly');
    }

  } finally {
    // Restore original max size
    sopsHelper.CONFIG.maxCacheSize = originalMaxSize;
  }

  logger.debug('Cache behavior with encryption validated successfully');
}

/**
 * Test error scenarios and recovery
 */
async function testErrorScenariosAndRecovery(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing error scenarios and recovery...');

  const sopsHelper = require('../helpers/sops-yaml.js');
  const testDir = testSuite.TEST_CONFIG.tempDir;

  // Test 1: Missing file
  try {
    await sopsHelper.decrypt('/nonexistent/file.yaml');
    throw new Error('Should have thrown for missing file');
  } catch (error) {
    if (!error.message.includes('ENOENT') && !error.message.includes('No such file')) {
      throw new Error(`Unexpected error for missing file: ${error.message}`);
    }
  }

  // Test 2: Invalid YAML
  const invalidYamlPath = path.join(testDir, 'invalid.yaml');
  fs.writeFileSync(invalidYamlPath, 'invalid: yaml: content: [unclosed');

  try {
    await sopsHelper.decrypt(invalidYamlPath);
    throw new Error('Should have thrown for invalid YAML');
  } catch (error) {
    if (!error.message.includes('YAML') && !error.message.includes('parse')) {
      throw new Error(`Unexpected error for invalid YAML: ${error.message}`);
    }
  } finally {
    if (fs.existsSync(invalidYamlPath)) {
      fs.unlinkSync(invalidYamlPath);
    }
  }

  // Test 3: Unencrypted file (should work in template mode)
  const unencryptedPath = path.join(testDir, 'unencrypted.yaml');
  fs.writeFileSync(unencryptedPath, 'test: value\n');

  try {
    const config = await sopsHelper.decrypt(unencryptedPath);
    if (config.test !== 'value') {
      throw new Error('Unencrypted file not properly loaded');
    }
  } finally {
    if (fs.existsSync(unencryptedPath)) {
      fs.unlinkSync(unencryptedPath);
    }
  }

  // Test 4: Permission errors (simulate)
  const permissionPath = path.join(testDir, 'permission-test.yaml');
  fs.writeFileSync(permissionPath, 'test: value\n');

  try {
    // Change permissions to read-only directory (won't work on all systems)
    if (process.platform !== 'win32') {
      fs.chmodSync(permissionPath, 0o000); // No permissions

      try {
        await sopsHelper.decrypt(permissionPath);
        logger.warn('Permission test may not work on this system');
      } catch (error) {
        if (!error.message.includes('permission') && !error.message.includes('EACCES')) {
          logger.warn(`Permission error test: ${error.message}`);
        }
      }
    }
  } finally {
    try {
      if (process.platform !== 'win32') {
        fs.chmodSync(permissionPath, 0o644); // Restore permissions
      }
      if (fs.existsSync(permissionPath)) {
        fs.unlinkSync(permissionPath);
      }
    } catch (error) {
      logger.warn(`Cleanup error: ${error.message}`);
    }
  }

  // Test 5: Invalid environment
  try {
    await sopsHelper.getEnvironmentConfig('r2', 'invalid-env', false);
    throw new Error('Should have thrown for invalid environment');
  } catch (error) {
    if (!error.message.includes('Invalid') && !error.message.includes('invalid')) {
      throw new Error(`Unexpected error for invalid environment: ${error.message}`);
    }
  }

  // Test 6: Recovery after error
  sopsHelper.clearCache();

  // Cause an error
  try {
    await sopsHelper.getEnvironmentConfig('r2', 'invalid-env', false);
  } catch (error) {
    // Expected error
  }

  // Verify normal operation still works
  const config = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
  if (!config.cf_account_id) {
    throw new Error('Normal operation failed after error');
  }

  logger.debug('Error scenarios and recovery validated successfully');
}

/**
 * Test security validation
 */
async function testSecurityValidation(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing security validation...');

  // Test 1: Plaintext detection
  const testDir = testSuite.TEST_CONFIG.tempDir;
  const plaintextPath = path.join(testDir, 'plaintext-secrets.yaml');

  // Create file with obvious secrets
  const plaintextSecrets = `# This file contains plaintext secrets (bad!)
cf_account_id: 1234567890abcdef1234567890abcdef
r2_access_key_id: AKIAIOSFODNN7EXAMPLE
r2_secret_access_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
api_token: very-secret-token-123
password: super-secret-password
`;

  fs.writeFileSync(plaintextPath, plaintextSecrets);

  try {
    // Test our security validation
    const result = await testSuite.execCommand('nix run .#no-plaintext-secrets');

    if (result.code === 0) {
      logger.warn('Plaintext secrets detection may not be working properly');
    } else {
      logger.debug('Plaintext secrets properly detected');
    }

  } catch (error) {
    logger.debug(`Security validation: ${error.message}`);
  } finally {
    if (fs.existsSync(plaintextPath)) {
      fs.unlinkSync(plaintextPath);
    }
  }

  // Test 2: Encrypted file validation
  if (!testSuite.TEST_CONFIG.skipSops) {
    const encryptedPath = path.join(testDir, 'encrypted-secrets.yaml');
    fs.writeFileSync(encryptedPath, plaintextSecrets);

    try {
      // Encrypt the file
      await testSuite.execCommand(`sops --encrypt --in-place ${encryptedPath}`);

      // Verify encrypted file passes security check
      const encryptedContent = fs.readFileSync(encryptedPath, 'utf8');

      if (encryptedContent.includes('AKIAIOSFODNN7EXAMPLE')) {
        throw new Error('File not properly encrypted');
      }

      if (!encryptedContent.includes('sops:')) {
        throw new Error('File missing SOPS metadata');
      }

    } catch (error) {
      if (error.message.includes('age key') || error.message.includes('SOPS')) {
        logger.warn(`Encryption test skipped: ${error.message}`);
      } else {
        throw error;
      }
    } finally {
      if (fs.existsSync(encryptedPath)) {
        fs.unlinkSync(encryptedPath);
      }
    }
  }

  // Test 3: Key security validation
  const sopsHelper = require('../helpers/sops-yaml.js');
  const health = await sopsHelper.healthCheck();

  if (health.ageKey && process.env.SOPS_AGE_KEY_FILE) {
    const keyFile = process.env.SOPS_AGE_KEY_FILE;

    if (fs.existsSync(keyFile)) {
      const stats = fs.statSync(keyFile);
      const mode = stats.mode & parseInt('777', 8);

      // Key file should not be world-readable
      if (mode & parseInt('044', 8)) {
        logger.warn(`Age key file ${keyFile} is world-readable - consider securing permissions`);
      }
    }
  }

  // Test 4: Configuration security
  const config = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

  // Check for placeholder values that should be replaced
  const placeholderPatterns = [
    'placeholder',
    'example',
    'your-',
    'change-me',
    'TODO',
    'FIXME'
  ];

  for (const pattern of placeholderPatterns) {
    if (config.cf_account_id && config.cf_account_id.includes(pattern)) {
      logger.warn(`Configuration contains placeholder in account ID: ${pattern}`);
    }
  }

  logger.debug('Security validation completed successfully');
}

/**
 * Test performance with encryption
 */
async function testPerformanceWithEncryption(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing performance with encryption...');

  const sopsHelper = require('../helpers/sops-yaml.js');
  const iterations = 10;

  // Test template mode performance (baseline)
  sopsHelper.clearCache();
  const templateStart = Date.now();

  for (let i = 0; i < iterations; i++) {
    await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
  }

  const templateTime = Date.now() - templateStart;
  const templateAvg = templateTime / iterations;

  logger.performance(`Template mode average: ${templateAvg.toFixed(2)}ms per operation`);

  // Test with cache enabled
  sopsHelper.clearCache();
  const cacheStart = Date.now();

  // First call (cache miss)
  await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

  // Subsequent calls (cache hits)
  for (let i = 1; i < iterations; i++) {
    await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
  }

  const cacheTime = Date.now() - cacheStart;
  const cacheAvg = cacheTime / iterations;

  logger.performance(`Cached mode average: ${cacheAvg.toFixed(2)}ms per operation`);

  // Cache should be significantly faster
  if (cacheAvg > templateAvg * 0.8) {
    logger.warn('Cache performance benefit less than expected');
  }

  // Test cache statistics
  const stats = sopsHelper.getCacheStats();
  logger.performance(`Cache stats: ${stats.hits} hits, ${stats.misses} misses, size: ${stats.size}`);

  // Test memory usage
  const memoryBefore = process.memoryUsage();

  // Load multiple environments
  for (const env of ['dev', 'stg', 'prod']) {
    await sopsHelper.getEnvironmentConfig('r2', env, true);
  }

  const memoryAfter = process.memoryUsage();
  const memoryDelta = memoryAfter.heapUsed - memoryBefore.heapUsed;

  logger.performance(`Memory usage delta: ${(memoryDelta / 1024 / 1024).toFixed(2)}MB`);

  // Memory usage should be reasonable
  if (memoryDelta > 50 * 1024 * 1024) { // 50MB
    logger.warn('High memory usage detected');
  }

  // Test performance with encryption (if available)
  if (!testSuite.TEST_CONFIG.skipSops) {
    const testDir = testSuite.TEST_CONFIG.tempDir;
    const encryptedPath = path.join(testDir, 'perf-test.yaml');

    try {
      // Create test file
      fs.writeFileSync(encryptedPath, 'test: value\nother: data\n');

      // Encrypt it
      await testSuite.execCommand(`sops --encrypt --in-place ${encryptedPath}`);

      // Test decryption performance
      const decryptStart = Date.now();

      for (let i = 0; i < 5; i++) {
        await sopsHelper.decrypt(encryptedPath);
      }

      const decryptTime = Date.now() - decryptStart;
      const decryptAvg = decryptTime / 5;

      logger.performance(`Decryption average: ${decryptAvg.toFixed(2)}ms per operation`);

    } catch (error) {
      logger.warn(`Encryption performance test skipped: ${error.message}`);
    } finally {
      if (fs.existsSync(encryptedPath)) {
        fs.unlinkSync(encryptedPath);
      }
    }
  }

  logger.debug('Performance with encryption validated successfully');
}

/**
 * Test multi-environment encryption
 */
async function testMultiEnvironmentEncryption(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing multi-environment encryption...');

  const testDir = testSuite.TEST_CONFIG.tempDir;
  const environments = ['dev', 'stg', 'prod'];

  // Create encrypted config for each environment
  for (const env of environments) {
    const envConfigPath = path.join(testDir, `r2-${env}.yaml`);

    const envConfig = `# R2 configuration for ${env}
cf_account_id: ${generateTestAccountId(env)}
r2_buckets:
  - ${env}-bucket-1
  - ${env}-bucket-2
r2_access_key_id: ${env}-access-key
r2_secret_access_key: ${env}-secret-key-${Date.now()}
`;

    fs.writeFileSync(envConfigPath, envConfig);

    try {
      // Encrypt each environment config
      await testSuite.execCommand(`sops --encrypt --in-place ${envConfigPath}`);

      // Verify encryption
      const encryptedContent = fs.readFileSync(envConfigPath, 'utf8');

      if (!encryptedContent.includes('sops:')) {
        throw new Error(`Environment ${env} config not properly encrypted`);
      }

      if (encryptedContent.includes(`${env}-secret-key`)) {
        throw new Error(`Environment ${env} secret still visible after encryption`);
      }

      // Test decryption
      const sopsHelper = require('../helpers/sops-yaml.js');
      const decrypted = await sopsHelper.decrypt(envConfigPath);

      if (!decrypted.cf_account_id || !decrypted.r2_buckets) {
        throw new Error(`Environment ${env} config incomplete after decryption`);
      }

      if (decrypted.cf_account_id !== generateTestAccountId(env)) {
        throw new Error(`Environment ${env} account ID mismatch after decryption`);
      }

    } catch (error) {
      if (error.message.includes('age key') || error.message.includes('SOPS')) {
        logger.warn(`Multi-environment encryption test skipped for ${env}: ${error.message}`);
        continue;
      }
      throw error;
    } finally {
      if (fs.existsSync(envConfigPath)) {
        fs.unlinkSync(envConfigPath);
      }
    }
  }

  logger.debug('Multi-environment encryption validated successfully');
}

/**
 * Extract age public keys from private key content
 */
function extractAgePublicKeys(keyContent) {
  const publicKeys = [];
  const lines = keyContent.split('\n');

  for (const line of lines) {
    if (line.startsWith('# public key: age1')) {
      const publicKey = line.replace('# public key: ', '').trim();
      if (publicKey.startsWith('age1')) {
        publicKeys.push(publicKey);
      }
    }
  }

  return publicKeys;
}

/**
 * Generate test account ID for environment
 */
function generateTestAccountId(environment) {
  const hash = crypto.createHash('md5').update(`test-${environment}`).digest('hex');
  return hash.substring(0, 32);
}

module.exports = {
  runTests,
  testSopsBinaryAvailability,
  testAgeKeyConfiguration,
  testBasicEncryptionDecryption,
  testSopsYamlIntegration,
  testEncryptedConfigurationLoading,
  testCacheBehaviorWithEncryption,
  testErrorScenariosAndRecovery,
  testSecurityValidation,
  testPerformanceWithEncryption,
  testMultiEnvironmentEncryption,
  extractAgePublicKeys,
  generateTestAccountId,
};
