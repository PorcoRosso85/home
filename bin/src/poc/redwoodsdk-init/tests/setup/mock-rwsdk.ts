// Mock for rwsdk modules
import { vi } from 'vitest';

// Mock rwsdk/worker
export const defineApp = vi.fn((handlers: any[]) => {
  return async (request: Request) => {
    // Simple mock implementation
    return new Response('Mock response');
  };
});

export const ErrorResponse = class extends Error {
  constructor(public message: string, public status: number = 500) {
    super(message);
  }
};

export const requestInfo = {
  request: new Request('http://localhost:3000'),
  response: {
    headers: new Headers()
  },
  headers: new Headers(),
  ctx: {
    user: null,
    session: null
  }
};

export type RequestInfo = typeof requestInfo;

// Mock rwsdk/router
export const route = vi.fn();
export const render = vi.fn();
export const prefix = vi.fn();

// Mock rwsdk/auth
export const defineDurableSession = vi.fn((config: any) => {
  return {
    load: vi.fn(),
    save: vi.fn(),
    destroy: vi.fn()
  };
});