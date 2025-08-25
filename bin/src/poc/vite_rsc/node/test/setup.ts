// Test setup file for Vitest
// Mock necessary globals and modules for RSC testing

// Mock import.meta.viteRsc for test environment
if (typeof globalThis !== 'undefined') {
  Object.defineProperty(globalThis, 'import', {
    value: {
      meta: {
        viteRsc: {
          loadModule: async () => ({
            handleSsr: async (stream: ReadableStream) => stream,
          }),
          loadBootstrapScriptContent: async () => '',
        },
      },
    },
  });
}