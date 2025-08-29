import { getEnv } from '../../lib/waku';

/**
 * Type definitions for environment variables
 */
export interface EnvironmentVariables {
  MAX_ITEMS: number;
  ENABLE_WASM_FROM_R2: boolean;
  R2_PUBLIC_URL: string;
  R2_WASM_URL: string;
  // Add more environment variables here as needed
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
  ENABLE_WASM_FROM_R2: {
    key: 'ENABLE_WASM_FROM_R2',
    parser: (value) => {
      const parsed = parsers.boolean(value);
      return parsed !== undefined ? parsed : false;
    },
    required: false,
    defaultValue: false,
  },
  R2_PUBLIC_URL: {
    key: 'R2_PUBLIC_URL',
    parser: (value) => {
      return value || '';
    },
    required: false,
    defaultValue: '',
  },
  R2_WASM_URL: {
    key: 'R2_WASM_URL',
    parser: (value) => {
      return value || '';
    },
    required: false,
    defaultValue: '',
  },
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
 * Returns fresh values each time (no caching to avoid global state)
 */
export function getConfig(): EnvironmentVariables {
  const config = {} as EnvironmentVariables;
  
  for (const key of Object.keys(variableConfigs) as Array<keyof EnvironmentVariables>) {
    config[key] = getVariable(key);
  }
  
  return config;
}

/**
 * Validate that all required environment variables are present and valid
 */
export function validateEnvironmentVariables(): { valid: boolean; errors: string[] } {
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

/**
 * Individual getters for convenience - each returns fresh values
 */
export const getMaxItems = (): number => getVariable('MAX_ITEMS');
export const getEnableWasmFromR2 = (): boolean => getVariable('ENABLE_WASM_FROM_R2');
export const getR2PublicUrl = (): string => getVariable('R2_PUBLIC_URL');
export const getR2WasmUrl = (): string => getVariable('R2_WASM_URL');

/**
 * Export variable getter for direct access when needed
 */
export { getVariable };