import { beforeAll, afterAll, afterEach } from 'vitest';
import { vi } from 'vitest';

// Global test setup
beforeAll(() => {
  // Setup global mocks for Cloudflare Workers environment
  globalThis.crypto = {
    ...globalThis.crypto,
    randomUUID: () => {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      });
    },
    getRandomValues: (array: any) => {
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 256);
      }
      return array;
    }
  } as any;

  // Mock console methods for cleaner test output
  globalThis.console = {
    ...console,
    log: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
    info: vi.fn(),
    debug: vi.fn()
  };

  // Mock fetch for API tests
  globalThis.fetch = vi.fn();

  // Set test environment variables
  process.env.NODE_ENV = 'test';
  process.env.WEBAUTHN_RP_ID = 'localhost';
  process.env.WEBAUTHN_APP_NAME = 'Test App';
});

afterAll(() => {
  // Cleanup
  vi.restoreAllMocks();
});

afterEach(() => {
  // Clear all mocks after each test
  vi.clearAllMocks();
});