#!/usr/bin/env -S deno run --allow-all --unstable-worker-options

/**
 * Simulate external package usage
 * This would be how other packages import kuzu_ts
 */

// Simulating an import from another package
import { 
  createDatabase, 
  createConnection,
  terminateWorker,
  isValidationError
} from "./mod_worker.ts";

// Or using full path as external packages would
// import { createDatabase } from "../../persistence/kuzu_ts/mod_worker.ts";

console.log("✅ Successfully imported kuzu_ts module");
console.log("✅ All exports are available:");
console.log("  - createDatabase:", typeof createDatabase);
console.log("  - createConnection:", typeof createConnection);
console.log("  - terminateWorker:", typeof terminateWorker);
console.log("  - isValidationError:", typeof isValidationError);

// Quick functional test
const db = await createDatabase(":memory:");
if (!isValidationError(db)) {
  console.log("✅ Database creation works");
  await db.close();
  terminateWorker();
}