---
url: https://github.com/wakujs/waku/issues/1245
saved_at: 2025-08-30T00:00:00Z
title: Support wasm files in Cloudflare build plugin #1245
domain: github.com
---

# Support wasm files in Cloudflare build plugin #1245

[@wesbos](https://github.com/wesbos) opened on Feb 18, 2025

## Description

I'm using a package - Shiki - which requires me to import a .wasm file since Cloudflare workers doesn't support inlined WASM binaries.

I've tried using this package: [https://github.com/hadeeb/vite-plugin-wasm/](https://github.com/hadeeb/vite-plugin-wasm/) but since there seems to be multiple Vite build steps as part of the Waku build, the file gets put in the dist/public/assets/ directory, and it's not found in the dist/assets directory where it's needed for the server component.

Cloudflare recently added support for wasm files in their own vite plugin. So I am wondering if Waku can also get this functionality, or somehow use the cloudflare vite plugin?

[cloudflare/workers-sdk#8031](https://github.com/cloudflare/workers-sdk/pull/8031)