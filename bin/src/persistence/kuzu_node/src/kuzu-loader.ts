/**
 * Minimal KuzuDB loader - returns appropriate module for environment
 */

export async function loadKuzu() {
  if (typeof window !== 'undefined') {
    return await import('kuzu-wasm');
  }
  return require('kuzu-wasm/nodejs');
}