DELETE AFTER MIGRATION IS COMPLETE

Title: Reset + Guardrails + Submission Template — Prevent Recurrence and Execute Safe 1.0 Split

Context
- A previous attempt modified TypeScript/Nix settings (e.g., `tsconfig.json`, flake lock updates) and introduced regressions.
- Phase 1.1 is already committed and valid; a reset is possible. We must prevent recurrence by defining hard guardrails and a no‑surprises execution path.

Part A — Reset to Known‑Good (Phase 1.1)
1) Identify the Phase 1.1 completion commit
   - Source: `docs/.receipts/1.1.done` → `commit_hash`
2) Create a safety branch from current head
   - `git checkout -b safety/hold-<date>`
3) Reset working tree to the 1.1 commit (non‑force on shared repos; coordinate if needed)
   - `git reset --hard <commit_hash>`
4) Verify green state
   - `nix run --no-write-lock-file .#check`
   - `nix run --no-write-lock-file .#build-snippet`
   - `nix run --no-write-lock-file .#build-sitemap`
   - `nix run --no-write-lock-file .#build-hreflang`

Part B — Guardrails (Do/Don’t) to Prevent Recurrence
Do
- Use `--no-write-lock-file` for all `nix run`/`nix flake check` invocations during migration.
- Keep `packages/**` and root `tsconfig.json` unchanged (freeze baseline).
- Isolate Node‑oriented scripts type settings (if needed) via a separate `tsconfig.scripts.json` rather than touching root `tsconfig.json`.
- Make changes only in the new `foundation-1.0/` directory until acceptance.

Don’t
- Do NOT edit: `tsconfig.json`, `packages/**`, `flake.lock` (unless an explicit “lock update” PR is requested).
- Do NOT change root flake checks other than making “phase guard” optional (functional checks must remain).
- Do NOT add `@types/node` globally or switch global compiler `types` — keep Node types local to script tooling only.

Part C — Execution Path (Non‑destructive)
1) 1.0 Flake (new): follow `docs/migration/SAFE-MIGRATION-1.0-SPLIT.md` Stage A.
   - Create `foundation-1.0/flake.nix` (devShell + apps: check/build-snippet/serve-examples + checks).
   - All paths reference `../packages` and `../examples` (no file moves).
2) Root (1.1 stays): keep sitemap/hreflang commands working as is.
3) Make phase guard optional: remove from required checks only after verifying functional checks are green.
4) Validate both flakes independently. Only then consider Stage D (optional physical moves).

Part D — Acceptance Gates (must be green)
- Root:
  - `nix run --no-write-lock-file .#build-sitemap` → `public/sitemap.xml` present (count > 0, valid `<loc>/<lastmod>`)
  - `nix run --no-write-lock-file .#build-hreflang` → hreflang outputs present and valid
  - `nix run --no-write-lock-file .#check` + `nix flake check` pass
- New 1.0 flake (`foundation-1.0/`):
  - `nix run --no-write-lock-file .#check` passes (packages/* only)
  - `nix run --no-write-lock-file .#build-snippet` produces ESM+IIFE
  - `nix run --no-write-lock-file .#serve-examples` serves `../examples/phase-1.0/`

Part E — Rollback Plan
- Revert the migration PR/commit. Because all changes are additive and confined to `foundation-1.0/` and optional check toggles, rollback is trivial.

Appendix — Submission Template (Developer must fill before execution)
1) Summary
- Goal: Split Phase 1.0 into `foundation-1.0/` flake without changing root behavior. Make phase guard optional.

2) Scope of Change
- Files to add (exact paths):
  - `foundation-1.0/flake.nix`
  - `foundation-1.0/README.md`
- Files to modify (if any):
  - Root `flake.nix` — ONLY to make phase guard optional (no other changes)
- Files explicitly NOT to touch:
  - `tsconfig.json`, `packages/**`, `flake.lock`, `public/**` (except generated outputs)

3) Commands (with `--no-write-lock-file`)
- Root validation: `nix run .#check`, `.#build-sitemap`, `.#build-hreflang`, `nix flake check`
- New flake: `cd foundation-1.0 && nix run .#check && nix run .#build-snippet && nix run .#serve-examples`

4) Risks & Mitigations
- Lock file churn → use `--no-write-lock-file`; separate PR for lock updates if required.
- TypeScript conflicts → no changes to root `tsconfig.json`; use dedicated `tsconfig.scripts.json` if needed.
- Command ambiguity → document both flakes’ commands in each README; different shell banners.

5) Acceptance Evidence
- Paste outputs: URL count in `public/sitemap.xml`, sizes of snippet ESM/IIFE, screenshots or logs of hreflang validation, both flakes’ command logs.

