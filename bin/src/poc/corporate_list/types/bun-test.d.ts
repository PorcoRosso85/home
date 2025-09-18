// Type declarations for bun:test module
declare module "bun:test" {
  export interface Matchers {
    toBe(expected: any): void
    toEqual(expected: any): void
    toBeTruthy(): void
    toBeFalsy(): void
    toBeGreaterThan(expected: number): void
    toBeGreaterThanOrEqual(expected: number): void
    toBeLessThan(expected: number): void
    toBeLessThanOrEqual(expected: number): void
    toContain(expected: any): void
    toHaveProperty(property: string): void
    toThrow(): void
    toThrowError(expected?: string | RegExp | Error): void
  }

  export interface ExpectStatic {
    (actual: any): Matchers
  }

  export const expect: ExpectStatic

  export function test(name: string, fn: () => void | Promise<void>): void
  export function describe(name: string, fn: () => void): void
  export function it(name: string, fn: () => void | Promise<void>): void
  export function beforeEach(fn: () => void | Promise<void>): void
  export function afterEach(fn: () => void | Promise<void>): void
  export function beforeAll(fn: () => void | Promise<void>): void
  export function afterAll(fn: () => void | Promise<void>): void
}