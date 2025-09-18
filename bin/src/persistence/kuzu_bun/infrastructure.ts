/**
 * Infrastructure: Environment-specific KuzuDB loading
 */

export type KuzuModule = {
  Database: any;
  Connection: any;
  close: () => Promise<void>;
};

export async function loadKuzu(): Promise<KuzuModule> {
  if (typeof window !== 'undefined') {
    return await import('kuzu-wasm');
  }
  return require('kuzu-wasm/nodejs');
}