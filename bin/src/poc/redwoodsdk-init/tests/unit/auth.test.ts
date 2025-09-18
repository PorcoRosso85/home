import { describe, it, expect, beforeEach, vi } from 'vitest';
import { generateRegistrationOptions, generateAuthenticationOptions } from '@simplewebauthn/server';
import { startPasskeyRegistration, startPasskeyLogin } from '../../src/app/pages/user/functions';

// Mock dependencies
vi.mock('@simplewebauthn/server');
vi.mock('rwsdk/worker', () => ({
  requestInfo: {
    request: new Request('http://localhost:3000'),
    response: {
      headers: new Headers()
    },
    headers: new Headers()
  }
}));
vi.mock('../../src/session/store', () => ({
  sessions: {
    save: vi.fn(),
    load: vi.fn()
  }
}));
vi.mock('cloudflare:workers', () => ({
  env: {
    WEBAUTHN_RP_ID: 'localhost',
    WEBAUTHN_APP_NAME: 'Test App'
  }
}));

describe('Authentication Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Passkey Registration', () => {
    it('should generate registration options with correct parameters', async () => {
      const mockOptions = {
        challenge: 'test-challenge',
        rpName: 'Test App',
        rpID: 'localhost',
        userName: 'testuser'
      };
      
      vi.mocked(generateRegistrationOptions).mockResolvedValue(mockOptions as any);
      
      const result = await startPasskeyRegistration('testuser');
      
      expect(generateRegistrationOptions).toHaveBeenCalledWith({
        rpName: expect.any(String),
        rpID: 'localhost',
        userName: 'testuser',
        authenticatorSelection: {
          residentKey: 'required',
          userVerification: 'preferred'
        }
      });
      
      expect(result).toEqual(mockOptions);
    });

    it('should save challenge to session', async () => {
      const mockOptions = {
        challenge: 'test-challenge-123'
      };
      
      vi.mocked(generateRegistrationOptions).mockResolvedValue(mockOptions as any);
      const { sessions } = await import('../../src/session/store');
      
      await startPasskeyRegistration('testuser');
      
      expect(sessions.save).toHaveBeenCalledWith(
        expect.any(Headers),
        { challenge: 'test-challenge-123' }
      );
    });
  });

  describe('Passkey Login', () => {
    it('should generate authentication options', async () => {
      const mockOptions = {
        challenge: 'login-challenge',
        rpID: 'localhost'
      };
      
      vi.mocked(generateAuthenticationOptions).mockResolvedValue(mockOptions as any);
      
      const result = await startPasskeyLogin();
      
      expect(generateAuthenticationOptions).toHaveBeenCalledWith({
        rpID: 'localhost',
        userVerification: 'preferred',
        allowCredentials: []
      });
      
      expect(result).toEqual(mockOptions);
    });

    it('should handle missing environment variables gracefully', async () => {
      // Test with undefined WEBAUTHN_RP_ID
      const originalEnv = process.env.WEBAUTHN_RP_ID;
      delete process.env.WEBAUTHN_RP_ID;
      
      const mockOptions = { challenge: 'test' };
      vi.mocked(generateAuthenticationOptions).mockResolvedValue(mockOptions as any);
      
      await expect(startPasskeyLogin()).resolves.toBeDefined();
      
      process.env.WEBAUTHN_RP_ID = originalEnv;
    });
  });
});