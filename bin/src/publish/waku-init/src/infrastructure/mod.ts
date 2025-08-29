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
  getVariable,
  type EnvironmentVariables,
} from './variables/env.js';

// R2 functionality can be added here in the future
// export { ... } from './r2/index.js';