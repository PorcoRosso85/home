#!/usr/bin/env bun
/**
 * Vessel for Bun with structured logging - 規約準拠版
 */
import { VesselLogger } from "./vessel_log.ts";

const logger = new VesselLogger("vessel");

async function main() {
  logger.debug("Reading script from stdin");
  const script = await Bun.stdin.text();
  logger.debug(`Script length: ${script.length} chars`);

  try {
    logger.debug("Executing script");
    
    // Create async function for top-level await support
    const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
    const func = new AsyncFunction("console", script);
    
    // Wrap console.log to use our logger
    const wrappedConsole = {
      ...console,
      log: (...args: any[]) => logger.output(args.join(" "))
    };
    
    await func(wrappedConsole);
    logger.debug("Script execution completed");
  } catch (error) {
    logger.error("Script execution failed", error);
    process.exit(1);
  }
}

main();