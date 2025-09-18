# Repository Guidelines

## Purpose
- この目的は、meからの目的とそのための指示を理解することと、`../claude.md`, `../cli-designer.sh.example`を使い外部Claude Code/Developerに実装・動作テストを依頼し、レビューすること。

## Project Structure & Module Organization
- Root docs: `instructions.md` (task list) and `status.md` (work log).
- Nix flake scaffold: `flake.nix` (dev/build entry; may be minimal).
- Generated artifacts: `.lsif-index.db/` is an index cache; do not edit by hand.
- If code is added later, place sources under `src/` and tests under `tests/`.

## Build, Test, and Development Commands
- `nix develop` — enter the dev shell (when `flake.nix` defines one).
- `nix build` — build the default package; use when the flake exposes outputs.
- `nix flake check` — run flake checks (format, tests, CI-style validations).
- If a Rust crate is introduced: `cargo build`, `cargo test` in the crate root.

## Coding Style & Naming Conventions
- Markdown: use fenced code blocks, `- ` for lists, wrap ~100 chars.
- Filenames: kebab-case for docs (e.g., `design-notes.md`).
- Nix: 2-space indent; format with `nix fmt` or `alejandra` (e.g., `nix run nixpkgs#alejandra -- .`).
- Shell scripts: include `set -euo pipefail`, name as `*.sh`, and keep POSIX where possible.

## Testing Guidelines
- No test harness exists here yet. When adding code:
  - Place tests in `tests/`; mirror module paths; aim for meaningful coverage.
  - Nix-based checks: add to `flake.nix` `checks` and run `nix flake check`.
  - Example Rust test file: `tests/language_detector_test.rs`.

## Commit & Pull Request Guidelines
- Use Conventional Commits with scopes seen in history (e.g., `feat(lsif-indexer): ...`, `fix(sops-flake): ...`, `docs(...): ...`, `refactor: ...`).
- Keep subjects imperative and ≤72 chars; add detail in the body if needed.
- PRs: include a clear description, linked issues, any config/security impacts, and screenshots when UI-related. Update `status.md` for notable work.

## Agent-Specific Instructions
- Treat `.lsif-index.db/` as generated; do not modify manually.
- Keep changes minimal and scoped; avoid unrelated refactors.
- Follow this AGENTS.md scope; prefer small patches with rationale.
- For multi-step work, share a brief plan and update it as you go.
