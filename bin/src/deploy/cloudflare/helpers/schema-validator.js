#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * JSON Schema Validator for Cloudflare Deployment SOT Configuration
 *
 * A comprehensive JSON Schema validation module using AJV (Another JSON Validator)
 * for validating Cloudflare deployment Source of Truth (SOT) configuration files.
 *
 * Features:
 * - AJV-based JSON Schema validation with detailed error reporting
 * - Custom validation for Cloudflare-specific requirements
 * - Graceful error handling with human-readable messages
 * - Support for both sync and async validation modes
 * - Extensible validation rules for future requirements
 * - Performance optimized with schema compilation caching
 * - Comprehensive logging for debugging and monitoring
 *
 * Usage:
 *   const validator = require('./helpers/schema-validator.js');
 *
 *   // Validate SOT configuration
 *   const result = validator.validateSOT(config);
 *   if (!result.valid) {
 *     console.error('Validation failed:', result.errors);
 *   }
 *
 *   // Validate with custom schema
 *   const result = validator.validateConfig(data, customSchema);
 *
 *   // Async validation with file loading
 *   const result = await validator.validateSOTFromFile('spec/dev/cloudflare.yaml');
 */

const fs = require('fs');
const path = require('path');

// Configuration constants
const CONFIG = {
  // Schema file paths
  defaultSchemaPath: './schemas/cloudflare.schema.json',
  schemasDirectory: './schemas',

  // Validation settings
  allErrors: true,          // Report all validation errors, not just the first
  verbose: true,            // Include detailed error information
  strict: true,             // Strict mode for schema validation
  removeAdditional: false,  // Don't modify the original data
  useDefaults: false,       // Don't apply default values from schema

  // Performance settings
  compilationTimeout: 5000, // 5 seconds max for schema compilation
  validationTimeout: 3000,  // 3 seconds max for validation

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
let compiledSchemas = new Map();
let validationStats = {
  totalValidations: 0,
  successfulValidations: 0,
  failedValidations: 0,
  cacheHits: 0,
  cacheMisses: 0
};

// Lazy load AJV to handle environments where it's not installed
let Ajv = null;
let addFormats = null;

/**
 * Initialize AJV with error handling for missing dependencies
 */
function initializeAJV() {
  if (Ajv !== null) {
    return Ajv;
  }

  try {
    Ajv = require('ajv');

    // Try to load ajv-formats for additional format validation
    try {
      addFormats = require('ajv-formats');
    } catch (error) {
      log('ajv-formats not available, using basic AJV validation only', 'WARN');
      addFormats = null;
    }

    log('AJV initialized successfully', 'DEBUG', {
      version: Ajv.version || 'unknown',
      formats: addFormats ? 'available' : 'unavailable'
    });

    return Ajv;
  } catch (error) {
    throw new Error(`AJV not available. Install with: npm install ajv ajv-formats. Error: ${error.message}`);
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
 * Load and parse JSON schema file
 */
function loadSchema(schemaPath) {
  const absolutePath = path.resolve(schemaPath);

  if (!fs.existsSync(absolutePath)) {
    throw new Error(`Schema file not found: ${absolutePath}`);
  }

  try {
    const schemaContent = fs.readFileSync(absolutePath, 'utf8');
    const schema = JSON.parse(schemaContent);

    log(`Schema loaded successfully`, 'DEBUG', {
      path: schemaPath,
      size: schemaContent.length,
      title: schema.title || 'untitled'
    });

    return schema;
  } catch (error) {
    throw new Error(`Failed to load schema from ${schemaPath}: ${error.message}`);
  }
}

/**
 * Create and configure AJV instance
 */
function createAJVInstance(options = {}) {
  const AjvClass = initializeAJV();

  const ajvOptions = {
    allErrors: CONFIG.allErrors,
    verbose: CONFIG.verbose,
    strict: CONFIG.strict,
    removeAdditional: CONFIG.removeAdditional,
    useDefaults: CONFIG.useDefaults,
    ...options
  };

  const ajv = new AjvClass(ajvOptions);

  // Add format validation if available
  if (addFormats) {
    addFormats(ajv);
    log('AJV formats added successfully', 'TRACE');
  }

  // Add custom keywords for Cloudflare-specific validation
  addCloudflareKeywords(ajv);

  log('AJV instance created', 'DEBUG', ajvOptions);

  return ajv;
}

/**
 * Add custom validation keywords for Cloudflare-specific requirements
 */
function addCloudflareKeywords(ajv) {
  // Custom keyword for validating R2 bucket names
  ajv.addKeyword({
    keyword: 'r2BucketName',
    type: 'string',
    compile: () => {
      return function validate(data) {
        if (typeof data !== 'string') {
          return false;
        }

        // R2 bucket naming rules:
        // - 3-63 characters long
        // - lowercase letters, numbers, hyphens, and periods
        // - must start and end with letter or number
        // - cannot contain consecutive periods
        // - cannot be formatted as IP address

        if (data.length < 3 || data.length > 63) {
          validate.errors = [{ message: 'R2 bucket name must be 3-63 characters long' }];
          return false;
        }

        if (!/^[a-z0-9]/.test(data) || !/[a-z0-9]$/.test(data)) {
          validate.errors = [{ message: 'R2 bucket name must start and end with letter or number' }];
          return false;
        }

        if (!/^[a-z0-9.-]+$/.test(data)) {
          validate.errors = [{ message: 'R2 bucket name can only contain lowercase letters, numbers, hyphens, and periods' }];
          return false;
        }

        if (/\.\./.test(data)) {
          validate.errors = [{ message: 'R2 bucket name cannot contain consecutive periods' }];
          return false;
        }

        // Simple IP address pattern check
        if (/^\d+\.\d+\.\d+\.\d+$/.test(data)) {
          validate.errors = [{ message: 'R2 bucket name cannot be formatted as IP address' }];
          return false;
        }

        return true;
      };
    }
  });

  // Custom keyword for validating Worker binding names
  ajv.addKeyword({
    keyword: 'workerBinding',
    type: 'string',
    compile: () => {
      return function validate(data) {
        if (typeof data !== 'string') {
          return false;
        }

        // Worker binding name rules:
        // - Must be valid JavaScript identifier
        // - Cannot be reserved words
        // - Cannot start with number

        if (!/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(data)) {
          validate.errors = [{ message: 'Worker binding name must be a valid JavaScript identifier' }];
          return false;
        }

        // Check against reserved JavaScript keywords
        const reservedWords = [
          'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 'default',
          'delete', 'do', 'else', 'export', 'extends', 'finally', 'for', 'function',
          'if', 'import', 'in', 'instanceof', 'let', 'new', 'return', 'super',
          'switch', 'this', 'throw', 'try', 'typeof', 'var', 'void', 'while',
          'with', 'yield', 'await', 'async'
        ];

        if (reservedWords.includes(data.toLowerCase())) {
          validate.errors = [{ message: `Worker binding name cannot be a reserved JavaScript keyword: ${data}` }];
          return false;
        }

        return true;
      };
    }
  });

  log('Custom Cloudflare validation keywords added', 'DEBUG');
}

/**
 * Compile schema with caching
 */
function compileSchema(schema, cacheKey) {
  // Check cache first
  if (compiledSchemas.has(cacheKey)) {
    validationStats.cacheHits++;
    log(`Using cached compiled schema`, 'TRACE', { cacheKey });
    return compiledSchemas.get(cacheKey);
  }

  validationStats.cacheMisses++;

  try {
    const ajv = createAJVInstance();
    const validate = ajv.compile(schema);

    // Cache the compiled schema
    compiledSchemas.set(cacheKey, validate);

    log(`Schema compiled and cached`, 'DEBUG', {
      cacheKey,
      cacheSize: compiledSchemas.size
    });

    return validate;
  } catch (error) {
    throw new Error(`Schema compilation failed: ${error.message}`);
  }
}

/**
 * Format validation errors into human-readable messages
 */
function formatValidationErrors(errors, dataPath = '') {
  if (!errors || errors.length === 0) {
    return [];
  }

  return errors.map(error => {
    const instancePath = error.instancePath || dataPath;
    const path = instancePath ? `${instancePath}` : 'root';

    let message = `${path}: ${error.message}`;

    // Add more context for specific error types
    if (error.keyword === 'required') {
      message = `${path}: Missing required property '${error.params.missingProperty}'`;
    } else if (error.keyword === 'additionalProperties') {
      message = `${path}: Unexpected property '${error.params.additionalProperty}'`;
    } else if (error.keyword === 'type') {
      message = `${path}: Expected ${error.params.type}, got ${typeof error.data}`;
    } else if (error.keyword === 'pattern') {
      message = `${path}: Value does not match pattern ${error.params.pattern}`;
    } else if (error.keyword === 'enum') {
      message = `${path}: Value must be one of: ${error.params.allowedValues.join(', ')}`;
    }

    // Add data context if available and relevant
    if (error.data !== undefined && typeof error.data !== 'object') {
      message += ` (value: ${JSON.stringify(error.data)})`;
    }

    return {
      path: instancePath,
      keyword: error.keyword,
      message: message,
      value: error.data,
      allowedValues: error.params?.allowedValues,
      originalError: error
    };
  });
}

/**
 * Main SOT validation function
 */
function validateSOT(config, options = {}) {
  const startTime = Date.now();
  validationStats.totalValidations++;

  try {
    // Load default schema if not provided
    const schemaPath = options.schemaPath || CONFIG.defaultSchemaPath;
    const schema = options.schema || loadSchema(schemaPath);

    // Generate cache key for schema
    const cacheKey = options.cacheKey || `sot-${schemaPath}`;

    // Compile schema
    const validate = compileSchema(schema, cacheKey);

    // Perform validation
    const isValid = validate(config);

    const duration = Date.now() - startTime;

    if (isValid) {
      validationStats.successfulValidations++;
      log(`SOT validation successful`, 'DEBUG', {
        duration: `${duration}ms`,
        configKeys: Object.keys(config || {}).length
      });

      return {
        valid: true,
        errors: [],
        warnings: [],
        duration,
        schema: schema.title || 'Cloudflare SOT Schema'
      };
    } else {
      validationStats.failedValidations++;
      const formattedErrors = formatValidationErrors(validate.errors);

      log(`SOT validation failed`, 'WARN', {
        duration: `${duration}ms`,
        errorCount: formattedErrors.length
      });

      return {
        valid: false,
        errors: formattedErrors,
        warnings: [],
        duration,
        schema: schema.title || 'Cloudflare SOT Schema'
      };
    }

  } catch (error) {
    validationStats.failedValidations++;
    const duration = Date.now() - startTime;

    log(`SOT validation error`, 'ERROR', {
      duration: `${duration}ms`,
      error: error.message
    });

    return {
      valid: false,
      errors: [{
        path: 'validation',
        keyword: 'system',
        message: `Validation system error: ${error.message}`,
        value: null,
        originalError: error
      }],
      warnings: [],
      duration,
      schema: 'Unknown'
    };
  }
}

/**
 * Validate configuration with custom schema
 */
function validateConfig(data, schema, options = {}) {
  return validateSOT(data, {
    ...options,
    schema: schema,
    cacheKey: options.cacheKey || `custom-${Date.now()}`
  });
}

/**
 * Validate SOT configuration from file
 */
async function validateSOTFromFile(filePath, options = {}) {
  try {
    // This function would integrate with sops-yaml.js
    // For now, we'll read the file directly
    const fileContent = fs.readFileSync(filePath, 'utf8');

    // Try to parse as JSON first, then YAML
    let config;
    try {
      config = JSON.parse(fileContent);
    } catch (jsonError) {
      // If not JSON, assume it's YAML and use a basic parser
      // In production, this would use the sops-yaml.js module
      throw new Error('YAML parsing not implemented in standalone mode. Use validateSOT() with pre-parsed config.');
    }

    return validateSOT(config, {
      ...options,
      cacheKey: `file-${filePath}`
    });

  } catch (error) {
    return {
      valid: false,
      errors: [{
        path: 'file',
        keyword: 'system',
        message: `File validation error: ${error.message}`,
        value: filePath,
        originalError: error
      }],
      warnings: [],
      duration: 0,
      schema: 'Unknown'
    };
  }
}

/**
 * Get validation statistics
 */
function getValidationStats() {
  const cacheSize = compiledSchemas.size;
  const totalRequests = validationStats.cacheHits + validationStats.cacheMisses;
  const cacheHitRate = totalRequests > 0 ? (validationStats.cacheHits / totalRequests * 100).toFixed(2) : '0.00';

  return {
    ...validationStats,
    cacheSize,
    cacheHitRate: `${cacheHitRate}%`,
    totalCacheRequests: totalRequests
  };
}

/**
 * Clear compiled schema cache
 */
function clearSchemaCache() {
  const cacheSize = compiledSchemas.size;
  compiledSchemas.clear();

  log(`Schema cache cleared`, 'DEBUG', { entriesRemoved: cacheSize });

  return cacheSize;
}

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
 * Health check for validation system
 */
function healthCheck() {
  const health = {
    timestamp: new Date().toISOString(),
    ajv: false,
    ajvFormats: false,
    defaultSchema: false,
    stats: getValidationStats(),
    errors: []
  };

  try {
    // Check AJV availability
    initializeAJV();
    health.ajv = true;

    if (addFormats) {
      health.ajvFormats = true;
    }
  } catch (error) {
    health.errors.push(`AJV initialization failed: ${error.message}`);
  }

  try {
    // Check default schema
    loadSchema(CONFIG.defaultSchemaPath);
    health.defaultSchema = true;
  } catch (error) {
    health.errors.push(`Default schema loading failed: ${error.message}`);
  }

  return health;
}

// Export all functions
module.exports = {
  // Main validation functions
  validateSOT,
  validateConfig,
  validateSOTFromFile,

  // Utility functions
  loadSchema,
  formatValidationErrors,
  getValidationStats,
  clearSchemaCache,
  setLogLevel,
  healthCheck,

  // Configuration
  CONFIG,

  // For testing and advanced usage
  _internal: {
    createAJVInstance,
    compileSchema,
    addCloudflareKeywords,
    initializeAJV
  }
};

// CLI support when called directly
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(`
JSON Schema Validator for Cloudflare SOT

Usage:
  node schema-validator.js <command> [options]

Commands:
  validate <file>           Validate SOT file against schema
  health                    Show validator health status
  stats                     Show validation statistics
  clear-cache              Clear compiled schema cache

Examples:
  node schema-validator.js validate spec/dev/cloudflare.yaml
  node schema-validator.js health
  node schema-validator.js stats
    `);
    process.exit(0);
  }

  const command = args[0];

  (async () => {
    try {
      switch (command) {
        case 'validate':
          if (args.length < 2) {
            throw new Error('File path required for validate command');
          }
          const result = await validateSOTFromFile(args[1]);
          console.log(JSON.stringify(result, null, 2));
          break;

        case 'health':
          const health = healthCheck();
          console.log(JSON.stringify(health, null, 2));
          break;

        case 'stats':
          const stats = getValidationStats();
          console.log(JSON.stringify(stats, null, 2));
          break;

        case 'clear-cache':
          const cleared = clearSchemaCache();
          console.log(`Cache cleared: ${cleared} entries removed`);
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