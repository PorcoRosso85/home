import { describe, it, expect } from 'vitest';

describe('Vitest Basic Test', () => {
  it('should work with simple assertions', () => {
    expect(1 + 1).toBe(2);
  });

  it('should handle async operations', async () => {
    const result = await Promise.resolve('hello');
    expect(result).toBe('hello');
  });
});