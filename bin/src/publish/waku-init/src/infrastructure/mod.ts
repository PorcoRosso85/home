/**
 * Infrastructure layer - Public API
 * 
 * This module provides the public interface for all infrastructure-related functionality.
 * It follows the conventions of:
 * - No global state
 * - Functions that return values
 * - Proper error handling for missing environment variables
 * - Type safety
 */

// Variables/Environment configuration
export {
  getConfig,
  validateEnvironmentVariables,
  getMaxItems,
  getEnableWasmFromR2,
  getR2PublicUrl,
  getR2WasmUrl,
  getStorageType,
  getVariable,
  type EnvironmentVariables,
  type StorageType,
} from './variables/env.js';

// Storage adapters
export { LogAdapter } from './storage/log-adapter.js';
export { R2Adapter } from './storage/r2-adapter.js';
export { MultiAdapter } from './storage/multi-adapter.js';

// Storage factory
export {
  createStorageAdapter,
  createStorageAdapterFromEnv,
  getStorageType as getStorageTypeFromFactory,
  type CreateStorageAdapterOptions,
} from './storage/factory.js';

// R2 functionality can be added here in the future
// export { ... } from './r2/index.js';