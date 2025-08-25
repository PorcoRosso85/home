/**
 * AsyncLocalStorage polyfill for Cloudflare Workers
 * Provides minimal but functional implementation for RSC context management
 */

class AsyncLocalStorage {
  constructor() {
    this.store = new WeakMap();
    this.currentContext = null;
  }

  /**
   * Run a function with a specific context store
   * @param {any} store - The context store to use during execution
   * @param {Function} callback - Function to execute with the store
   * @param {...any} args - Arguments to pass to the callback
   * @returns {any} Result of the callback execution
   */
  run(store, callback, ...args) {
    const previousContext = this.currentContext;
    this.currentContext = store;
    
    try {
      return callback(...args);
    } finally {
      this.currentContext = previousContext;
    }
  }

  /**
   * Get the current context store
   * @returns {any} Current context store or undefined
   */
  getStore() {
    return this.currentContext;
  }

  /**
   * Enter a new async context (for promise-based async operations)
   * @param {any} store - The context store
   * @param {Function} callback - Async function to execute
   * @param {...any} args - Arguments for the callback
   * @returns {Promise<any>} Promise resolving to callback result
   */
  async enterWith(store, callback, ...args) {
    return this.run(store, callback, ...args);
  }

  /**
   * Disable context propagation (no-op in this polyfill)
   */
  disable() {
    this.currentContext = null;
  }

  /**
   * Snapshot current context (simplified implementation)
   * @returns {Function} Function that runs callback with captured context
   */
  snapshot() {
    const capturedContext = this.currentContext;
    return (callback, ...args) => {
      const previousContext = this.currentContext;
      this.currentContext = capturedContext;
      try {
        return callback(...args);
      } finally {
        this.currentContext = previousContext;
      }
    };
  }
}

// Create and export singleton instance
const asyncLocalStorage = new AsyncLocalStorage();

// Make it globally available for Workers environment
if (typeof globalThis !== 'undefined' && !globalThis.AsyncLocalStorage) {
  globalThis.AsyncLocalStorage = AsyncLocalStorage;
}

export { AsyncLocalStorage, asyncLocalStorage };
export default asyncLocalStorage;