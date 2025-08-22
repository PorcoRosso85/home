# Repository Guidelines

This contributor guide describes how to work with the Codex repository: project structure, common commands, coding standards, testing, and contribution practices.

## Project Structure & Module Organization
- `flake.nix` - Nix flake entry point, defines dev shell, build, and checks.
- `src/` - source code for the application/library.
- `tests/` - tests mirroring the `src/` layout.
- `bin/` - executable launchers or CLI entry points.
- `nix/` - extra flake modules, overlays, or build helpers.
- Optional: `docs/` and `assets/`.

- Modules should be cohesive; group by feature under `src/<feature>/` (e.g., `src/core/`, `src/api/`).

## Build, Test, and Development Commands
- `nix develop` - enter a reproducible dev shell with the toolchain.
- `nix build` - build the default package; outputs `./result`.
- `nix run` - run the default app/CLI as defined in the flake.
- `nix flake check` - run format, lint, and tests checks.

- Run tests with language-specific tooling inside the dev shell, e.g.:
  - Python: `pytest tests/`
  - JS/TS: `npm test` (or `pnpm test`) in the repo root.

## Coding Style & Naming Conventions
- Indentation: 2 spaces for JSON/YAML/TS; 4 spaces for Python.
- Filenames: `snake_case` for libraries/modules; `kebab-case` for executables/scripts.
- Identifiers: `PascalCase` for classes/types; `camelCase` for functions/vars (JS/TS); `snake_case` for Python.
- Formatting: use project-provided formatters in the dev shell; Python: Black; TS: Prettier.

## Testing Guidelines
- Tests live under `tests/` mirroring `src/`.
- Naming: `test_*.py` (Python) or `*.test.ts`/`*.spec.ts` (TS).
- Coverage: prefer meaningful coverage on core modules and error paths.
- Run locally via language-specific commands (see Build section).

## Commit & Pull Request Guidelines
- Commits use Conventional Commits, e.g. `feat(core): add config loader`, `fix(nix): pin runner version`.
- PRs: clear description, link issues (Closes #...), list changes, add test notes, and include UI screenshots if applicable.

## Security & Configuration Tips
- Do not commit secrets; use environment vars and `.env` (git-ignored).
- Use `direnv` + `use flake` for shells; ensure commands also work with `nix build`/`nix run`.

