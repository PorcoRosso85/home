import { getEnv } from './waku';

/**
 * Type definitions for environment variables
 */
interface EnvironmentVariables {
  MAX_ITEMS: number;
  // Add more environment variables here as needed
  // EXAMPLE_STRING?: string;
  // EXAMPLE_BOOLEAN?: boolean;
}

/**
 * Configuration for environment variable parsing and validation
 */
interface VariableConfig<T> {
  key: string;
  parser: (value: string | undefined) => T;
  required?: boolean;
  defaultValue?: T;
}

/**
 * Parser functions for different data types
 */
const parsers = {
  string: (value: string | undefined): string | undefined => value,
  number: (value: string | undefined): number | undefined => {
    if (value === undefined) return undefined;
    const parsed = Number.parseInt(value, 10);
    if (isNaN(parsed)) throw new Error(`Invalid number: ${value}`);
    return parsed;
  },
  boolean: (value: string | undefined): boolean | undefined => {
    if (value === undefined) return undefined;
    const lower = value.toLowerCase();
    if (lower === 'true' || lower === '1') return true;
    if (lower === 'false' || lower === '0') return false;
    throw new Error(`Invalid boolean: ${value}`);
  },
} as const;

/**
 * Environment variable configurations
 */
const variableConfigs: {
  [K in keyof EnvironmentVariables]: VariableConfig<EnvironmentVariables[K]>
} = {
  MAX_ITEMS: {
    key: 'MAX_ITEMS',
    parser: (value) => {
      const parsed = parsers.number(value);
      if (parsed === undefined) return 10; // Default value
      if (parsed < 1) throw new Error('MAX_ITEMS must be greater than 0');
      return parsed;
    },
    required: false,
    defaultValue: 10,
  },
  // Add more configurations here as needed
};

/**
 * Get a typed environment variable with validation
 */
function getVariable<K extends keyof EnvironmentVariables>(
  key: K
): EnvironmentVariables[K] {
  const config = variableConfigs[key];
  const rawValue = getEnv(config.key);
  
  try {
    const parsedValue = config.parser(rawValue);
    
    if (parsedValue === undefined) {
      if (config.required && config.defaultValue === undefined) {
        throw new Error(`Required environment variable ${config.key} is not set`);
      }
      return config.defaultValue as EnvironmentVariables[K];
    }
    
    return parsedValue;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown parsing error';
    throw new Error(`Error parsing environment variable ${config.key}: ${errorMessage}`);
  }
}

/**
 * Get all environment variables as a typed configuration object
 */
function getConfig(): EnvironmentVariables {
  const config = {} as EnvironmentVariables;
  
  for (const key of Object.keys(variableConfigs) as Array<keyof EnvironmentVariables>) {
    config[key] = getVariable(key);
  }
  
  return config;
}

/**
 * Validate that all required environment variables are present and valid
 */
function validateEnvironmentVariables(): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  for (const [key, config] of Object.entries(variableConfigs) as Array<
    [keyof EnvironmentVariables, VariableConfig<any>]
  >) {
    if (config.required) {
      try {
        getVariable(key);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        errors.push(errorMessage);
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}

// Create a singleton config object for efficient access
let cachedConfig: EnvironmentVariables | null = null;

/**
 * Get the cached configuration object (lazy initialization)
 */
export function config(): EnvironmentVariables {
  if (cachedConfig === null) {
    cachedConfig = getConfig();
  }
  return cachedConfig;
}

// Export individual getters for convenience
export const variables = {
  maxItems: () => getVariable('MAX_ITEMS'),
  // Add more getters here as needed
} as const;

// Export utilities
export { getVariable, validateEnvironmentVariables };

// Export types for external use
export type { EnvironmentVariables };