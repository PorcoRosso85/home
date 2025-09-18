# log_ts - TypeScript Logging Implementation

TypeScript implementation of the universal log API for telemetry purposes.

## Overview

This module provides a standardized logging interface following Domain-Driven Design (DDD) principles. It implements a universal logging API that can be used across different TypeScript/Deno projects for consistent telemetry and log management.

## Installation

### As a Flake Input

Add to your `flake.nix`:

```nix
{
  inputs = {
    log-ts.url = "path:/home/nixos/bin/src/telemetry/log_ts";
    # or from a git repository:
    # log-ts.url = "github:your-org/your-repo?dir=src/telemetry/log_ts";
  };
}
```

### Direct Import

For Deno projects, you can directly import the module:

```typescript
import { log } from "file:///home/nixos/bin/src/telemetry/log_ts/mod.ts";
```

## Usage

### Basic Logging

```typescript
import { log } from "@telemetry/log";

// Log an info message
await log({
  level: "INFO",
  message: "Application started",
  timestamp: new Date().toISOString()
});

// Log with additional context
await log({
  level: "ERROR",
  message: "Failed to process request",
  timestamp: new Date().toISOString(),
  context: {
    requestId: "123456",
    userId: "user-789"
  }
});
```

### JSONL Conversion

The module also provides utilities for converting log data to JSONL format:

```typescript
import { toJsonl } from "@telemetry/log";

const logData = {
  level: "INFO",
  message: "Test message",
  timestamp: new Date().toISOString()
};

const jsonlString = toJsonl(logData);
```

## Available Commands

Run these commands using `nix run`:

- `nix run .#test` - Run the test suite
- `nix run .#check` - Type check the module
- `nix run .#repl` - Start a Deno REPL with the module pre-loaded
- `nix run .#readme` - Display this README

## Development

### Prerequisites

- Nix with flakes enabled
- Deno (provided by the development shell)

### Getting Started

1. Enter the development shell:
   ```bash
   nix develop
   ```

2. Run tests:
   ```bash
   deno test --allow-read --allow-env
   ```

3. Type check:
   ```bash
   deno check mod.ts
   ```

## Architecture

The module follows DDD principles with clear layer separation:

- **Domain Layer** (`domain.ts`): Core types and business logic
- **Application Layer** (`application.ts`): Use cases and orchestration
- **Infrastructure Layer** (`infrastructure.ts`): External interactions
- **Variables** (`variables.ts`): Configuration and environment handling

## API Reference

### Types

- `LogData`: The main type representing log entry data

### Functions

- `log(data: LogData): Promise<void>`: Main logging function
- `toJsonl(data: LogData): string`: Convert log data to JSONL format

## Integration Examples

See `example_usage.md` for detailed integration examples including:
- Using as a flake input
- Using the overlay
- Direct TypeScript imports
- Import map configuration

## License

See the project root for license information.