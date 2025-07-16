// Contract Service POC - Main exports
export { handler } from "./main.ts";
export { Registry } from "./registry.ts";
export { Router } from "./router.ts";
export { Matcher } from "./matcher.ts";
export { Transformer } from "./transformer.ts";
export { initDatabase, Database } from "./kuzu_wrapper.ts";

// Export all types
export type {
  Result,
  RegistryError,
  RouterError,
  TransformerError,
  JsonSchema,
  ProviderRegistration,
  ConsumerRegistration,
  SchemaData
} from "./types.ts";