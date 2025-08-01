# Kuzu TypeScript Hybrid Runtime Architecture

## Overview

This project implements a hybrid runtime architecture using both Deno (server) and Bun (client) to leverage the strengths of each platform while working with KuzuDB.

## Runtime Responsibilities

### Server (Deno)
- **Primary Role**: Handles direct KuzuDB operations through native bindings
- **Key Responsibilities**:
  - Database initialization and management
  - Direct query execution against local KuzuDB files
  - Data persistence and transaction management
  - Serving as the source of truth for database state

### Client (Bun)
- **Primary Role**: Provides fast client-side operations and testing capabilities
- **Key Responsibilities**:
  - WebAssembly-based KuzuDB operations for browser compatibility
  - Rapid test execution and development workflows
  - Client-side data validation and preprocessing
  - Integration testing with the Deno server

## Runtime Selection Rationale

### Why Deno for Server?
1. **Native Bindings**: Superior support for KuzuDB's native bindings
2. **Security**: Built-in permission system for database file access
3. **Stability**: Mature runtime for server-side operations
4. **TypeScript First**: Native TypeScript support without configuration

### Why Bun for Client?
1. **Performance**: Fastest JavaScript runtime for test execution
2. **WebAssembly Support**: Excellent WASM performance for browser scenarios
3. **Developer Experience**: Quick iteration cycles during development
4. **Compatibility**: Better npm package compatibility for client libraries

## Future Direction

### Current State (Recommended)
Maintain the hybrid architecture to:
- Leverage platform-specific optimizations
- Support both native and WASM deployments
- Enable flexible deployment strategies

### Potential Unification Considerations
Future evaluation criteria for runtime unification:
1. **Bun Native Bindings**: When Bun's native module support matures
2. **Deno WASM Performance**: If Deno's WASM performance matches Bun
3. **Feature Parity**: When both runtimes achieve equivalent capabilities

### Migration Strategy
If unification becomes beneficial:
1. Evaluate performance benchmarks
2. Assess feature compatibility
3. Create migration tooling
4. Maintain backward compatibility during transition

## Architecture Benefits

1. **Separation of Concerns**: Clear boundaries between server and client logic
2. **Performance Optimization**: Each component uses the most suitable runtime
3. **Flexibility**: Can deploy server-only, client-only, or hybrid configurations
4. **Future-Proof**: Easy to adapt as runtime capabilities evolve