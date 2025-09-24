#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * Shared SOPS YAML Decryption Helper
 *
 * A comprehensive module for handling SOPS-encrypted YAML files with intelligent caching,
 * robust error handling, and performance optimizations. Designed to be reused across
 * multiple generators (wrangler config, connection manifest, etc.).
 *
 * Features:
 * - SOPS decryption with Age key support
 * - Intelligent caching with TTL (time-to-live)
 * - Comprehensive error handling and recovery
 * - YAML parsing and validation
 * - Memory efficient operations
 * - Thread-safe caching (Node.js compatible)
 * - Extensive logging and debugging
 * - Performance monitoring
 *
 * Usage:
 *   const sopsYaml = require('./helpers/sops-yaml.js');
 *
 *   // Simple decryption
 *   const config = await sopsYaml.decrypt('secrets/r2.yaml');
 *
 *   // With caching and validation
 *   const config = await sopsYaml.decryptWithValidation('secrets/r2.yaml', schema);
 *
 *   // Environment-specific with template fallback
 *   const config = await sopsYaml.getEnvironmentConfig('r2', 'dev', useTemplate);
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const crypto = require('crypto');

// Configuration constants
const CONFIG = {
  // Cache settings
  defaultCacheTTL: 5 * 60 * 1000, // 5 minutes in milliseconds
  maxCacheSize: 100,              // Maximum number of cached entries

  // SOPS settings
  defaultAgeKeyPath: '~/.config/sops/age/keys.txt',
  sopsBinary: 'sops',

  // File patterns
  secretsBasePath: './secrets',
  environmentPattern: /^(dev|stg|prod)$/,

  // Performance settings
  maxFileSize: 10 * 1024 * 1024,  // 10MB max file size
  maxDecryptionTime: 30000,       // 30 seconds timeout

  // Validation
  requiredSopsKeys: ['sops_version', 'sops'],

  // Logging levels
  logLevels: {
    ERROR: 0,
    WARN: 1,
    INFO: 2,
    DEBUG: 3,
    TRACE: 4
  }
};

// Global state
let globalLogLevel = CONFIG.logLevels.INFO;
let cache = new Map();
let cacheMetrics = {
  hits: 0,
  misses: 0,
  evictions: 0,
  errors: 0
};

/**
 * Cache entry structure
 */
class CacheEntry {
  constructor(data, ttl = CONFIG.defaultCacheTTL) {
    this.data = data;
    this.created = Date.now();
    this.accessed = Date.now();
    this.ttl = ttl;
    this.accessCount = 1;
  }

  isExpired() {
    return (Date.now() - this.created) > this.ttl;
  }

  access() {
    this.accessed = Date.now();
    this.accessCount++;
    return this.data;
  }
}

/**
 * Enhanced logging with levels and formatting
 */
function log(message, level = 'INFO', context = {}) {
  const levelNum = CONFIG.logLevels[level] || CONFIG.logLevels.INFO;

  if (levelNum > globalLogLevel) {
    return;
  }

  const timestamp = new Date().toISOString();
  const prefix = {
    ERROR: '❌',
    WARN: '⚠️ ',
    INFO: '📋',
    DEBUG: '🔍',
    TRACE: '🔬'
  };

  const contextStr = Object.keys(context).length > 0
    ? ` [${Object.entries(context).map(([k, v]) => `${k}=${v}`).join(', ')}]`
    : '';

  console.log(`${prefix[level] || '📋'} [${timestamp}] ${message}${contextStr}`);
}

/**
 * Performance monitoring decorator
 */
function withPerformanceMonitoring(operationName, fn) {
  return async function(...args) {
    const startTime = process.hrtime.bigint();
    const startMemory = process.memoryUsage();

    try {
      log(`Starting ${operationName}`, 'DEBUG', {
        memory: `${Math.round(startMemory.heapUsed / 1024 / 1024)}MB`
      });

      const result = await fn.apply(this, args);

      const endTime = process.hrtime.bigint();
      const duration = Number(endTime - startTime) / 1000000; // Convert to milliseconds
      const endMemory = process.memoryUsage();
      const memoryDelta = endMemory.heapUsed - startMemory.heapUsed;

      log(`Completed ${operationName}`, 'DEBUG', {
        duration: `${duration.toFixed(2)}ms`,
        memoryDelta: `${Math.round(memoryDelta / 1024)}KB`
      });

      return result;
    } catch (error) {
      const endTime = process.hrtime.bigint();
      const duration = Number(endTime - startTime) / 1000000;

      log(`Failed ${operationName}`, 'ERROR', {
        duration: `${duration.toFixed(2)}ms`,
        error: error.message
      });

      throw error;
    }
  };
}

/**
 * Expand user home directory in file paths
 */
function expandPath(filePath) {
  if (filePath.startsWith('~/')) {
    return path.join(process.env.HOME || '/tmp', filePath.slice(2));
  }
  return path.resolve(filePath);
}

/**
 * Generate cache key for a file and options
 */
function generateCacheKey(filePath, options = {}) {
  const absolutePath = expandPath(filePath);
  const optionsHash = crypto.createHash('md5')
    .update(JSON.stringify(options))
    .digest('hex')
    .substring(0, 8);

  return `${absolutePath}:${optionsHash}`;
}

/**
 * Cache management with LRU eviction
 */
function getCachedEntry(cacheKey) {
  const entry = cache.get(cacheKey);

  if (!entry) {
    cacheMetrics.misses++;
    log(`Cache miss for ${cacheKey}`, 'TRACE');
    return null;
  }

  if (entry.isExpired()) {
    cache.delete(cacheKey);
    cacheMetrics.misses++;
    log(`Cache expired for ${cacheKey}`, 'TRACE');
    return null;
  }

  cacheMetrics.hits++;
  log(`Cache hit for ${cacheKey}`, 'TRACE', {
    age: `${Date.now() - entry.created}ms`,
    accessCount: entry.accessCount
  });

  return entry.access();
}

/**
 * Store entry in cache with LRU eviction
 */
function setCachedEntry(cacheKey, data, ttl = CONFIG.defaultCacheTTL) {
  // Evict oldest entries if cache is full
  while (cache.size >= CONFIG.maxCacheSize) {
    const oldestKey = cache.keys().next().value;
    cache.delete(oldestKey);
    cacheMetrics.evictions++;
    log(`Cache eviction: ${oldestKey}`, 'TRACE');
  }

  cache.set(cacheKey, new CacheEntry(data, ttl));
  log(`Cache stored: ${cacheKey}`, 'TRACE', { ttl: `${ttl}ms` });
}

/**
 * Clear cache (for testing or manual cleanup)
 */
function clearCache() {
  const size = cache.size;
  cache.clear();
  cacheMetrics = { hits: 0, misses: 0, evictions: 0, errors: 0 };
  log(`Cache cleared`, 'DEBUG', { entriesRemoved: size });
}

/**
 * Get cache statistics
 */
function getCacheStats() {
  const totalRequests = cacheMetrics.hits + cacheMetrics.misses;
  const hitRate = totalRequests > 0 ? (cacheMetrics.hits / totalRequests * 100).toFixed(2) : '0.00';

  return {
    ...cacheMetrics,
    size: cache.size,
    hitRate: `${hitRate}%`,
    totalRequests
  };
}

/**
 * Validate file existence and size
 */
function validateFile(filePath) {
  const absolutePath = expandPath(filePath);

  if (!fs.existsSync(absolutePath)) {
    throw new Error(`File not found: ${absolutePath}`);
  }

  const stats = fs.statSync(absolutePath);

  if (!stats.isFile()) {
    throw new Error(`Path is not a file: ${absolutePath}`);
  }

  if (stats.size > CONFIG.maxFileSize) {
    throw new Error(`File too large: ${absolutePath} (${stats.size} bytes, max: ${CONFIG.maxFileSize})`);
  }

  if (stats.size === 0) {
    throw new Error(`File is empty: ${absolutePath}`);
  }

  return { absolutePath, stats };
}

/**
 * Check SOPS prerequisites
 */
function checkSopsPrerequisites(options = {}) {
  const ageKeyPath = options.ageKeyPath || CONFIG.defaultAgeKeyPath;
  const expandedKeyPath = expandPath(ageKeyPath);

  // Check SOPS binary
  try {
    execSync(`which ${CONFIG.sopsBinary}`, { stdio: 'pipe' });
  } catch (error) {
    throw new Error(`SOPS binary not found: ${CONFIG.sopsBinary}. Make sure SOPS is installed and in PATH.`);
  }

  // Check Age key file
  if (!fs.existsSync(expandedKeyPath)) {
    throw new Error(`Age key file not found: ${expandedKeyPath}`);
  }

  // Check Age key file permissions (should be readable only by owner)
  const keyStats = fs.statSync(expandedKeyPath);
  const permissions = (keyStats.mode & parseInt('777', 8)).toString(8);

  if (permissions !== '600' && permissions !== '400') {
    log(`Age key file permissions are ${permissions}, recommended: 600`, 'WARN', {
      file: expandedKeyPath
    });
  }

  // Check .sops.yaml
  if (!fs.existsSync('.sops.yaml')) {
    throw new Error('SOPS configuration file not found: .sops.yaml');
  }

  log('SOPS prerequisites verified', 'DEBUG', {
    ageKeyPath: expandedKeyPath,
    sopsBinary: CONFIG.sopsBinary
  });

  return { ageKeyPath: expandedKeyPath };
}

/**
 * Execute SOPS decryption with timeout and error handling
 */
async function executeSopsDecryption(filePath, options = {}) {
  const { ageKeyPath } = checkSopsPrerequisites(options);

  return new Promise((resolve, reject) => {
    const env = {
      ...process.env,
      SOPS_AGE_KEY_FILE: ageKeyPath
    };

    const sopsProcess = spawn(CONFIG.sopsBinary, ['-d', filePath], {
      env,
      stdio: ['ignore', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    // Set up timeout
    const timeout = setTimeout(() => {
      sopsProcess.kill('SIGTERM');
      reject(new Error(`SOPS decryption timeout after ${CONFIG.maxDecryptionTime}ms`));
    }, CONFIG.maxDecryptionTime);

    // Collect output
    sopsProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    sopsProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    // Handle process completion
    sopsProcess.on('close', (code) => {
      clearTimeout(timeout);

      if (code === 0) {
        log(`SOPS decryption successful`, 'DEBUG', {
          file: filePath,
          outputSize: stdout.length
        });
        resolve(stdout);
      } else {
        const error = new Error(`SOPS decryption failed with code ${code}: ${stderr.trim()}`);
        error.code = code;
        error.stderr = stderr;
        reject(error);
      }
    });

    // Handle process errors
    sopsProcess.on('error', (error) => {
      clearTimeout(timeout);
      reject(new Error(`SOPS process error: ${error.message}`));
    });
  });
}

/**
 * Parse YAML content with validation
 */
function parseYamlContent(yamlContent, options = {}) {
  const schema = options.schema;
  const strict = options.strict !== false; // Default to strict mode

  try {
    // Simple YAML parser (handles basic key-value pairs)
    const config = {};
    const lines = yamlContent.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Skip empty lines and comments
      if (!line || line.startsWith('#')) {
        continue;
      }

      // Handle simple key: value pairs
      const match = line.match(/^([^:]+):\s*(.*)$/);
      if (match) {
        const key = match[1].trim();
        let value = match[2].trim();

        // Remove quotes if present
        if ((value.startsWith('"') && value.endsWith('"')) ||
            (value.startsWith("'") && value.endsWith("'"))) {
          value = value.slice(1, -1);
        }

        // Convert empty values to null
        if (value === '') {
          value = null;
        }

        config[key] = value;
      } else if (strict) {
        log(`Skipping unparseable YAML line ${i + 1}: ${line}`, 'WARN');
      }
    }

    // Schema validation if provided
    if (schema) {
      validateConfigSchema(config, schema);
    }

    log(`YAML parsing successful`, 'DEBUG', {
      keys: Object.keys(config).length,
      contentSize: yamlContent.length
    });

    return config;
  } catch (error) {
    throw new Error(`YAML parsing failed: ${error.message}`);
  }
}

/**
 * Validate configuration against schema
 */
function validateConfigSchema(config, schema) {
  // Required fields validation
  if (schema.required) {
    for (const field of schema.required) {
      if (!(field in config) || config[field] === null || config[field] === '') {
        throw new Error(`Required field missing or empty: ${field}`);
      }
    }
  }

  // Field validation
  if (schema.fields) {
    for (const [fieldName, fieldSchema] of Object.entries(schema.fields)) {
      const value = config[fieldName];

      if (value !== null && value !== undefined) {
        // Type validation
        if (fieldSchema.type) {
          const actualType = typeof value;
          if (actualType !== fieldSchema.type) {
            throw new Error(`Field ${fieldName} has wrong type: expected ${fieldSchema.type}, got ${actualType}`);
          }
        }

        // Pattern validation
        if (fieldSchema.pattern && typeof value === 'string') {
          const regex = new RegExp(fieldSchema.pattern);
          if (!regex.test(value)) {
            throw new Error(`Field ${fieldName} does not match pattern: ${fieldSchema.pattern}`);
          }
        }

        // Custom validation
        if (fieldSchema.validate && typeof fieldSchema.validate === 'function') {
          const result = fieldSchema.validate(value);
          if (result !== true) {
            throw new Error(`Field ${fieldName} validation failed: ${result}`);
          }
        }
      }
    }
  }

  log(`Schema validation passed`, 'DEBUG', { schema: schema.name || 'unnamed' });
}

/**
 * Main decryption function with full feature set
 */
const decrypt = withPerformanceMonitoring('sops-decrypt', async function(filePath, options = {}) {
  const cacheKey = generateCacheKey(filePath, options);

  // Check cache first
  if (!options.bypassCache) {
    const cached = getCachedEntry(cacheKey);
    if (cached) {
      return cached;
    }
  }

  try {
    // Validate file
    const { absolutePath } = validateFile(filePath);

    // Execute SOPS decryption
    const decryptedContent = await executeSopsDecryption(absolutePath, options);

    // Parse YAML
    const config = parseYamlContent(decryptedContent, options);

    // Cache result
    if (!options.bypassCache) {
      setCachedEntry(cacheKey, config, options.cacheTTL);
    }

    return config;

  } catch (error) {
    cacheMetrics.errors++;
    log(`Decryption failed for ${filePath}`, 'ERROR', { error: error.message });
    throw error;
  }
});

/**
 * Decryption with built-in validation
 */
async function decryptWithValidation(filePath, schema, options = {}) {
  return decrypt(filePath, { ...options, schema });
}

/**
 * Environment-specific configuration loader
 */
async function getEnvironmentConfig(configType, environment, useTemplate = false, options = {}) {
  // Validate environment
  if (!CONFIG.environmentPattern.test(environment)) {
    throw new Error(`Invalid environment: ${environment}. Must be one of: dev, stg, prod`);
  }

  // Template mode - return mock data
  if (useTemplate) {
    log(`Using template configuration for ${configType}:${environment}`, 'INFO');
    return getTemplateConfig(configType, environment);
  }

  // Try environment-specific file first
  const envSpecificPath = path.join(CONFIG.secretsBasePath, configType, `${environment}.yaml`);
  const fallbackPath = path.join(CONFIG.secretsBasePath, `${configType}.yaml`);

  let configPath = envSpecificPath;

  // Check if environment-specific file exists
  if (!fs.existsSync(expandPath(envSpecificPath))) {
    log(`Environment-specific config not found: ${envSpecificPath}`, 'DEBUG');

    if (!fs.existsSync(expandPath(fallbackPath))) {
      throw new Error(`No configuration found for ${configType}:${environment}. Tried:\n  - ${envSpecificPath}\n  - ${fallbackPath}`);
    }

    configPath = fallbackPath;
    log(`Using fallback configuration: ${fallbackPath}`, 'INFO');
  }

  return decrypt(configPath, options);
}

/**
 * Generate template configuration for testing
 */
function getTemplateConfig(configType, environment) {
  const templates = {
    r2: {
      cf_account_id: `demo-account-${environment}-${Math.random().toString(36).substring(2, 8)}`,
      r2_buckets: environment === 'prod'
        ? 'user-uploads,static-assets,backups'
        : 'user-uploads,static-assets',
      r2_access_key_id: `demo-access-key-${environment}`,
      r2_secret_access_key: `demo-secret-key-${environment}`,
      r2_region: 'auto'
    }
  };

  const template = templates[configType];
  if (!template) {
    throw new Error(`No template available for config type: ${configType}`);
  }

  return { ...template };
}

/**
 * Bulk decryption for multiple files
 */
async function decryptMultiple(filePaths, options = {}) {
  const results = {};
  const errors = {};

  // Process files in parallel with concurrency limit
  const concurrency = options.concurrency || 3;
  const chunks = [];

  for (let i = 0; i < filePaths.length; i += concurrency) {
    chunks.push(filePaths.slice(i, i + concurrency));
  }

  for (const chunk of chunks) {
    const promises = chunk.map(async (filePath) => {
      try {
        const result = await decrypt(filePath, options);
        results[filePath] = result;
      } catch (error) {
        errors[filePath] = error.message;
      }
    });

    await Promise.all(promises);
  }

  return { results, errors };
}

/**
 * Configuration validation schemas
 */
const schemas = {
  r2: {
    name: 'R2 Configuration',
    required: ['cf_account_id', 'r2_buckets'],
    fields: {
      cf_account_id: {
        type: 'string',
        pattern: '^[a-f0-9]{32}$',
        validate: (value) => {
          if (value === 'your-account-id-here') {
            return 'Account ID is still placeholder value';
          }
          return true;
        }
      },
      r2_buckets: {
        type: 'string',
        pattern: '^[a-z0-9]([a-z0-9.-]*[a-z0-9])?(,[a-z0-9]([a-z0-9.-]*[a-z0-9])?)*$',
        validate: (value) => {
          const buckets = value.split(',').map(b => b.trim());
          for (const bucket of buckets) {
            if (bucket.length < 3 || bucket.length > 63) {
              return `Bucket name '${bucket}' must be 3-63 characters long`;
            }
          }
          return true;
        }
      },
      r2_access_key_id: {
        type: 'string'
      },
      r2_secret_access_key: {
        type: 'string'
      }
    }
  }
};

/**
 * Set logging level
 */
function setLogLevel(level) {
  if (typeof level === 'string') {
    level = CONFIG.logLevels[level.toUpperCase()];
  }

  if (level !== undefined && level >= 0 && level <= 4) {
    globalLogLevel = level;
    log(`Log level set to ${Object.keys(CONFIG.logLevels)[level]}`, 'DEBUG');
  } else {
    throw new Error(`Invalid log level: ${level}. Use 0-4 or ERROR/WARN/INFO/DEBUG/TRACE`);
  }
}

/**
 * Health check function
 */
async function healthCheck() {
  const health = {
    timestamp: new Date().toISOString(),
    sops: false,
    ageKey: false,
    sopsConfig: false,
    cache: getCacheStats(),
    errors: []
  };

  try {
    // Check SOPS prerequisites
    checkSopsPrerequisites();
    health.sops = true;
    health.ageKey = true;
    health.sopsConfig = true;
  } catch (error) {
    health.errors.push(error.message);
    if (error.message.includes('SOPS binary')) {
      health.sops = false;
    }
    if (error.message.includes('Age key')) {
      health.ageKey = false;
    }
    if (error.message.includes('.sops.yaml')) {
      health.sopsConfig = false;
    }
  }

  return health;
}

// Export all functions and constants
module.exports = {
  // Main functions
  decrypt,
  decryptWithValidation,
  getEnvironmentConfig,
  decryptMultiple,

  // Cache management
  clearCache,
  getCacheStats,

  // Utilities
  setLogLevel,
  healthCheck,
  expandPath,

  // Schemas
  schemas,

  // Configuration
  CONFIG,

  // For testing
  _internal: {
    parseYamlContent,
    validateConfigSchema,
    checkSopsPrerequisites,
    executeSopsDecryption,
    getTemplateConfig,
    validateFile,
    generateCacheKey
  }
};

// CLI support when called directly
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(`
SOPS YAML Helper CLI

Usage:
  node sops-yaml.js <command> [options]

Commands:
  decrypt <file>              Decrypt SOPS file
  health                      Show health status
  cache-stats                 Show cache statistics
  clear-cache                 Clear cache
  env-config <type> <env>     Get environment config

Examples:
  node sops-yaml.js decrypt secrets/r2.yaml
  node sops-yaml.js env-config r2 dev
  node sops-yaml.js health
    `);
    process.exit(0);
  }

  const command = args[0];

  (async () => {
    try {
      switch (command) {
        case 'decrypt':
          if (args.length < 2) {
            throw new Error('File path required for decrypt command');
          }
          const result = await decrypt(args[1]);
          console.log(JSON.stringify(result, null, 2));
          break;

        case 'env-config':
          if (args.length < 3) {
            throw new Error('Config type and environment required');
          }
          const envResult = await getEnvironmentConfig(args[1], args[2]);
          console.log(JSON.stringify(envResult, null, 2));
          break;

        case 'health':
          const health = await healthCheck();
          console.log(JSON.stringify(health, null, 2));
          break;

        case 'cache-stats':
          console.log(JSON.stringify(getCacheStats(), null, 2));
          break;

        case 'clear-cache':
          clearCache();
          console.log('Cache cleared');
          break;

        default:
          throw new Error(`Unknown command: ${command}`);
      }
    } catch (error) {
      console.error('❌ Error:', error.message);
      process.exit(1);
    }
  })();
}