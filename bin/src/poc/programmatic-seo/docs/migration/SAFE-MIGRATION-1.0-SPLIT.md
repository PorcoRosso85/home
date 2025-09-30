DELETE AFTER MIGRATION IS COMPLETE

Title: Safe Migration Plan — Split Phase 1.0 into an Independent Flake, Keep 1.1 Integrated, De‑scope Phase Guard

Objective
- Cleanly separate Phase 1.0 (paste‑only measurement + JSON‑LD) into its own flake without breaking current workflows.
- Keep Phase 1.1 (static sitemap/hreflang) integrated in the current flake.
- De‑scope phase guard (governance) from this directory with zero impact on functional checks.

Scope (in /home/nixos/bin/src/poc/programmatic-seo)
- Split only build/dev tooling for Phase 1.0 into a new sibling directory (independent flake).
- Keep all code and outputs working during migration; no destructive moves until acceptance.
- Remove phase guard checks from flake checks; leave docs as historical reference; optional: keep scripts for CI migration.

Out of Scope
- Cloudflare/Workers deployment (Phase 1.2). It will be implemented as a separate flake later.
- Changing library APIs (measurement/seo) — no interface changes.

Constraints & Principles
- SRP/KISS/YAGNI/DRY/SOLID compliant: one flake per runtime boundary; reuse shared code via relative paths or flake inputs.
- No downtime of existing commands: `nix run .#check`, `.#build-snippet`, `.#serve-examples`, `.#build-sitemap`, `.#build-hreflang` must continue to work in root.
- Rollbackable: a single revert restores pre‑migration behavior.

High‑Level Strategy
1) Create a new directory `foundation-1.0/` with an independent flake exporting devShell + apps (check/build-snippet/serve-examples) and type/checks reused from root.
2) Reference shared code (packages/measurement, packages/seo, examples/phase-1.0, public/robots|gsc) by relative paths — do NOT move files initially.
3) Validate the new flake works end‑to‑end; keep root flake unchanged at this stage.
4) De‑scope phase guard in root flake: drop `phase-guard` from checks; keep functional checks (tsc/build/sitemap/hreflang).
5) Optional finalization: once stable, gradually relocate 1.0 assets out of root (git mv), update paths, and prune duplicates.

Migration Steps (Plan Only — do not delete anything until Acceptance)

Stage A — Prepare New 1.0 Flake (non‑destructive)
1. Create folder: `foundation-1.0/`
2. Add `foundation-1.0/flake.nix` with:
   - devShell: Node 22 + TypeScript + esbuild + miniserve
   - apps: `check` (tsc --noEmit on ../packages/**/*), `build-snippet` (esbuild on ../packages/measurement/snippet.ts), `serve-examples` (serve ../examples/phase-1.0)
   - checks: tsc/build artifacts existence
   - Note: all paths reference the parent repo (`..`) — no file moves yet.
3. Add `foundation-1.0/README.md` with usage (nix develop/run) and supported commands; clearly state no Cloudflare dependencies.
4. Acceptance for Stage A:
   - `cd foundation-1.0 && nix run .#check` passes
   - `nix run .#build-snippet` produces `foundation-1.0/dist/measurement/snippet.{esm,iife}.js` (or writes to ../dist as explicitly designed)
   - `nix run .#serve-examples` serves ../examples/phase-1.0/

Stage B — Keep Root 1.1 Integrated (no changes to behavior)
5. Root flake remains the “main” flake for Phase 1.1 — scripts/build-sitemap.ts, build-hreflang.ts, and public outputs remain in place.
6. Ensure root commands still pass:
   - `nix run .#build-sitemap`, `nix run .#build-hreflang`, `nix flake check`

Stage C — De‑scope Phase Guard (governance → optional)
7. In root `flake.nix` checks, remove `phase-guard` from required checks (keep tsc/build/sitemap/hreflang validations). Leave scripts/docs under docs/PHASE_* for reference.
8. Optional (later): move governance to CI (PR template + required jobs) so this repo only enforces functional checks.
9. Acceptance for Stage C:
   - `nix flake check` passes without phase guard
   - All functional validations remain green

Stage D — (Optional) Finalize Split by Moving Files
10. After Stage A/B/C are green and used for N days, physically move 1.0 assets if you want:
    - Move `packages/measurement`, `packages/seo`, `examples/phase-1.0`, and minimal `public/{robots.txt,gsc-verification.html}` into `foundation-1.0/`.
    - Update paths in `foundation-1.0/flake.nix` and (if needed) root docs.
    - Verify both flakes independently.
11. Acceptance for Stage D:
    - `cd foundation-1.0 && nix run .#check && nix run .#build-snippet && nix run .#serve-examples`
    - `cd .. && nix run .#build-sitemap && nix run .#build-hreflang && nix flake check`

Rollout & Rollback
- Rollout sequence: A → B → C (stop here if satisfied) → D (optional)
- Rollback: revert the migration commit(s). Because Stage A–C are non‑destructive, simple git revert restores prior behavior.
- Data safety: no prod data involved; all artifacts are build outputs.

Risks & Mitigations
- Path resolution errors across flakes → Mitigation: use explicit relative paths (`../packages/...`, `../examples/...`). Run checks locally on both flakes.
- Duplicate commands confusion → Mitigation: document commands in each flake README; different echo banners in devShell.
- Phase guard removal reduces governance → Mitigation: move guard logic to CI (PR checks) before removing from required checks.

Acceptance Criteria (Migration Complete)
1. Two independent dev environments:
   - Root flake (Phase 1.1) passes ts/build/sitemap/hreflang checks.
   - foundation-1.0 flake passes ts/build-snippet checks and serves examples.
2. No command regressions versus pre‑migration (root flake still green).
3. Phase guard is optional (not a required root check); docs/scripts preserved or moved to CI.

Action Checklist (for the implementer)
- [ ] Create `foundation-1.0/flake.nix` with devShell/apps/checks
- [ ] Add `foundation-1.0/README.md` with usage
- [ ] Validate Stage A acceptance items
- [ ] Confirm root flake Phase 1.1 commands still pass
- [ ] Remove `phase-guard` from root checks (keep sitemap/hreflang validations)
- [ ] Decide whether to finalize Stage D (physical move) or keep path‑based reuse
- [ ] Update docs/README-PHASES.md to reflect split boundary (1.0 separate flake; 1.1 stays)

Notes
- Keeping path‑based reuse (no physical move) is the lowest‑risk split and satisfies SRP/KISS/YAGNI/DRY/SOLID.
- Physical moves can be postponed until 1.2 is in progress or CI is ready.
