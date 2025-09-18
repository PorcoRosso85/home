/**
 * Email Worker Tests
 * Tests for pure email routing functionality (forward/reject)
 */

import { describe, test, expect, beforeEach } from 'vitest';

// Mock ForwardableEmailMessage
class MockEmailMessage {
  from: string;
  to: string;
  headers: Headers;
  private _forwarded: boolean = false;
  private _rejected: boolean = false;
  private _rejectReason?: string;
  private _forwardedTo?: string;

  constructor(from: string, to: string, headers?: Record<string, string>) {
    this.from = from;
    this.to = to;
    this.headers = new Headers(headers || {});
  }

  async raw(): Promise<ArrayBuffer> {
    const content = `From: ${this.from}\nTo: ${this.to}\n\nTest message`;
    return new TextEncoder().encode(content).buffer;
  }

  setReject(reason: string): void {
    this._rejected = true;
    this._rejectReason = reason;
  }

  async forward(to: string, headers?: Headers): Promise<void> {
    this._forwarded = true;
    this._forwardedTo = to;
  }

  get isForwarded(): boolean {
    return this._forwarded;
  }

  get isRejected(): boolean {
    return this._rejected;
  }

  get rejectReason(): string | undefined {
    return this._rejectReason;
  }

  get forwardedTo(): string | undefined {
    return this._forwardedTo;
  }
}

// Import the worker
import worker from '../src/index';

describe('Email Worker Routing', () => {
  let env: any;
  let ctx: any;

  beforeEach(() => {
    env = {};
    ctx = {
      waitUntil: (promise: Promise<any>) => {},
      passThroughOnException: () => {}
    };
  });

  describe('Allowlist functionality', () => {
    test('emails from allowlisted addresses should be forwarded', async () => {
      const message = new MockEmailMessage('trusted@example.com', 'user@domain.com');
      
      await worker.email(message as any, env, ctx);
      
      expect(message.isForwarded).toBe(true);
      expect(message.forwardedTo).toBe('inbox@example.com');
      expect(message.isRejected).toBe(false);
    });

    test('emails from non-allowlisted addresses should be rejected', async () => {
      const message = new MockEmailMessage('unknown@example.com', 'user@domain.com');
      
      await worker.email(message as any, env, ctx);
      
      expect(message.isRejected).toBe(true);
      expect(message.rejectReason).toBe('Address not allowed');
      expect(message.isForwarded).toBe(false);
    });

    test('multiple allowlisted addresses should work', async () => {
      const message = new MockEmailMessage('friend@example.com', 'user@domain.com');
      
      await worker.email(message as any, env, ctx);
      
      expect(message.isForwarded).toBe(true);
      expect(message.forwardedTo).toBe('inbox@example.com');
    });
  });

  describe('Edge cases', () => {
    test('empty from address should be rejected', async () => {
      const message = new MockEmailMessage('', 'user@domain.com');
      
      await worker.email(message as any, env, ctx);
      
      expect(message.isRejected).toBe(true);
      expect(message.rejectReason).toBe('Address not allowed');
    });

    test('case sensitivity in email addresses', async () => {
      const message = new MockEmailMessage('TRUSTED@EXAMPLE.COM', 'user@domain.com');
      
      await worker.email(message as any, env, ctx);
      
      // Current implementation is case-sensitive
      expect(message.isRejected).toBe(true);
      expect(message.rejectReason).toBe('Address not allowed');
    });
  });
});