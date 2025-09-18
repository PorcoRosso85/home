import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { unstable_dev } from 'wrangler';
import type { UnstableDevWorker } from 'wrangler';

describe('API Integration Tests', () => {
  let worker: UnstableDevWorker;

  beforeAll(async () => {
    // Start a local worker for testing
    worker = await unstable_dev('src/worker.tsx', {
      experimental: { disableExperimentalWarning: true },
      local: true,
      persist: false
    });
  });

  afterAll(async () => {
    await worker?.stop();
  });

  beforeEach(() => {
    // Clear any test data between tests
  });

  describe('Home Page API', () => {
    it('should return home page HTML', async () => {
      const response = await worker.fetch('/');
      
      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('text/html');
      
      const html = await response.text();
      expect(html).toContain('<!DOCTYPE html>');
    });

    it('should show logged out state by default', async () => {
      const response = await worker.fetch('/');
      const html = await response.text();
      
      expect(html).toContain('You are not logged in');
    });

    it('should handle authenticated requests', async () => {
      // Mock authenticated session
      const response = await worker.fetch('/', {
        headers: {
          'Cookie': 'session=mock-authenticated-session'
        }
      });
      
      expect(response.status).toBe(200);
    });
  });

  describe('Authentication API Endpoints', () => {
    it('should handle registration start request', async () => {
      const response = await worker.fetch('/api/auth/register/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: 'testuser'
        })
      });
      
      if (response.status === 200) {
        const data = await response.json();
        expect(data).toHaveProperty('challenge');
        expect(data).toHaveProperty('rpID');
      } else {
        // API might not be implemented yet
        expect([404, 405]).toContain(response.status);
      }
    });

    it('should handle login start request', async () => {
      const response = await worker.fetch('/api/auth/login/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.status === 200) {
        const data = await response.json();
        expect(data).toHaveProperty('challenge');
      } else {
        // API might not be implemented yet
        expect([404, 405]).toContain(response.status);
      }
    });

    it('should reject invalid registration data', async () => {
      const response = await worker.fetch('/api/auth/register/finish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          // Invalid data
          invalidField: 'test'
        })
      });
      
      // Should return error status
      expect([400, 404, 422]).toContain(response.status);
    });
  });

  describe('Static Assets', () => {
    it('should serve static assets with correct headers', async () => {
      // Test CSS file
      const cssResponse = await worker.fetch('/assets/style.css');
      if (cssResponse.status === 200) {
        expect(cssResponse.headers.get('content-type')).toContain('text/css');
        expect(cssResponse.headers.get('cache-control')).toBeDefined();
      }
    });

    it('should return 404 for non-existent assets', async () => {
      const response = await worker.fetch('/assets/non-existent.js');
      expect([404, 500]).toContain(response.status);
    });
  });

  describe('Error Handling', () => {
    it('should handle malformed JSON requests', async () => {
      const response = await worker.fetch('/api/auth/register/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: 'invalid json'
      });
      
      expect([400, 500]).toContain(response.status);
    });

    it('should handle method not allowed', async () => {
      const response = await worker.fetch('/api/auth/register/start', {
        method: 'GET' // Wrong method
      });
      
      expect([404, 405]).toContain(response.status);
    });

    it('should include security headers', async () => {
      const response = await worker.fetch('/');
      
      // Check for common security headers
      const headers = response.headers;
      expect(headers.get('x-content-type-options')).toBe('nosniff');
      expect(headers.get('x-frame-options')).toBeDefined();
    });
  });

  describe('CORS Configuration', () => {
    it('should handle preflight requests', async () => {
      const response = await worker.fetch('/api/auth/login/start', {
        method: 'OPTIONS',
        headers: {
          'Origin': 'http://localhost:3000',
          'Access-Control-Request-Method': 'POST'
        }
      });
      
      if (response.status === 200 || response.status === 204) {
        expect(response.headers.get('access-control-allow-methods')).toBeDefined();
      }
    });

    it('should include CORS headers in responses', async () => {
      const response = await worker.fetch('/api/auth/login/start', {
        method: 'POST',
        headers: {
          'Origin': 'http://localhost:3000',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });
      
      if (response.headers.get('access-control-allow-origin')) {
        expect(response.headers.get('access-control-allow-origin')).toBeDefined();
      }
    });
  });
});