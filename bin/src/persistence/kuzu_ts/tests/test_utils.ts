import { existsSync } from "jsr:@std/fs@^1.0.0";

const TEMP_TEST_DIR = "./test_temp";

export function ensureTempDir(): string {
  if (!existsSync(TEMP_TEST_DIR)) {
    Deno.mkdirSync(TEMP_TEST_DIR, { recursive: true });
  }
  return TEMP_TEST_DIR;
}

export function cleanupTempDir(): void {
  if (existsSync(TEMP_TEST_DIR)) {
    Deno.removeSync(TEMP_TEST_DIR, { recursive: true });
  }
}