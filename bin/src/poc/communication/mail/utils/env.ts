/**
 * 環境変数バリデーション
 * セキュリティ規約に準拠
 */

import { z } from "https://deno.land/x/zod@v3.22.4/mod.ts";
import { Result } from "./result.ts";

const envSchema = z.object({
  GOOGLE_CLIENT_ID: z.string().min(1),
  GOOGLE_CLIENT_SECRET: z.string().min(1),
  TOKEN_FILE: z.string().default(".gmail_tokens.json"),
  LOG_LEVEL: z.enum(["trace", "debug", "info", "warn", "error", "fatal"]).default("info")
});

export type EnvConfig = z.infer<typeof envSchema>;

export function loadEnv(): Result<EnvConfig> {
  try {
    const env = envSchema.parse({
      GOOGLE_CLIENT_ID: Deno.env.get("GOOGLE_CLIENT_ID"),
      GOOGLE_CLIENT_SECRET: Deno.env.get("GOOGLE_CLIENT_SECRET"),
      TOKEN_FILE: Deno.env.get("TOKEN_FILE"),
      LOG_LEVEL: Deno.env.get("LOG_LEVEL")
    });
    
    return Result.ok(env);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const missingVars = error.errors
        .filter(e => e.code === "invalid_type" && e.received === "undefined")
        .map(e => e.path.join("."));
      
      return Result.error(
        "ENV_VALIDATION_ERROR",
        `Missing required environment variables: ${missingVars.join(", ")}`,
        error.errors
      );
    }
    
    return Result.error(
      "ENV_LOAD_ERROR",
      "Failed to load environment variables",
      error
    );
  }
}