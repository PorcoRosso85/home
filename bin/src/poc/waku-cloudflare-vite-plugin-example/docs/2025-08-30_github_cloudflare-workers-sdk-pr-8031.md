---
url: https://github.com/cloudflare/workers-sdk/pull/8031
saved_at: 2025-08-30T00:00:00Z
title: Support WebAssembly modules #8031
domain: github.com
---

# Support WebAssembly modules #8031

[@jamesopstad](https://github.com/jamesopstad) opened on Feb 5, 2025 • Merged on Feb 10, 2025

## Description

Fixes [#7851](https://github.com/cloudflare/workers-sdk/issues/7851). Partially addresses [#8022](https://github.com/cloudflare/workers-sdk/issues/8022).

This adds support for Wasm in the Vite plugin. Imported Wasm modules are loaded via the module fallback service in dev and included as part of the bundle in build.

I've prioritised Wasm first as users are asking for it. Once this PR is merged, however, I will create a follow up PR that generalises the approach to include `CompiledWasm`, `Text` and `Data` modules defined by the user's `rules`.

## Key Changes

- Support for WebAssembly modules in @cloudflare/vite-plugin
- Wasm modules loaded via module fallback service in dev
- Wasm modules included as part of the bundle in build
- Applies to Worker environments only

## Implementation Details

- The plugin handles `.wasm` imports
- Emits modules as assets and replaces import paths
- Works with both dev and build targets
- Uses Vite's normalizePath for cross-platform compatibility

## Testing

- Added test playground with Wasm examples
- Prisma test included to validate real-world usage
- Tests for both development and build modes

## Changeset

- @cloudflare/vite-plugin: Minor version bump

## Related Issues

- Fixes #7851
- Partially addresses #8022
- Referenced in wakujs/waku#1245

## Notes from Discussion

@wesbos asked about making the plugin agnostic to other Vite setups for use with Waku. 

@jamesopstad responded:
> We would love to properly support using the Cloudflare Vite plugin with Waku in the future but it's not something that will work at the moment, I'm afraid. The Wasm support is also not something that could easily be extracted into a standalone plugin at present.

The Waku team appears to be working on their own solution for integrating @cloudflare/vite-plugin.