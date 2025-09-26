# Repository Guidelines

## Project Structure & Module Organization
- `flake.nix`: Nix flake entry; defines dev shell, build, checks.
- `src/`: application/library code grouped by feature (e.g., `src/core/`, `src/api/`).
- `tests/`: mirrors `src/` layout for unit/integration tests.
- `bin/`: CLI entry points or launchers (kebab-case filenames).
- `nix/`: extra flake modules, overlays, build helpers.
- Optional: `docs/`, `assets/` for documentation and static files.

## Build, Test, and Development Commands
- `nix develop`: enter reproducible dev shell with toolchain.
- `nix build`: build default package; output symlink at `./result`.
- `nix run`: run the default app/CLI defined by the flake.
- `nix flake check`: run format, lint, and tests as configured.
- Inside dev shell:
  - Python tests: `pytest tests/`
  - JS/TS tests: `npm test` (or `pnpm test`)

## Coding Style & Naming Conventions
- Indentation: 2 spaces for JSON/YAML/TS; 4 spaces for Python.
- Filenames: snake_case for libs/modules; kebab-case for executables/scripts.
- Identifiers: PascalCase for classes/types; camelCase for JS/TS functions/vars; snake_case for Python.
- Formatting: use project formatters in dev shell (Python: Black; TS: Prettier). Run `nix flake check` before pushing.

## Testing Guidelines
- Location: tests live under `tests/` mirroring `src/` structure.
- Naming: Python `test_*.py`; JS/TS `*.test.ts` or `*.spec.ts`.
- Coverage: prioritize core modules, edge cases, and error paths.
- Run locally via language-specific commands (see above) inside `nix develop`.

## Commit & Pull Request Guidelines
- Commits: use Conventional Commits, e.g., `feat(core): add config loader`, `fix(nix): pin runner version`.
- PRs: include clear description, linked issues (e.g., “Closes #123”), bullet list of changes, test notes, and screenshots for UI changes.
- Keep PRs focused and small; update or add tests with behavior changes.

## Security & Configuration Tips
- Never commit secrets. Use environment variables and `.env` files (git-ignored).
- Prefer `direnv` with `use flake` for shells; verify workflows also run via `nix build`/`nix run`.
- Reproducibility: document non-obvious system assumptions in `docs/` and prefer Nix-based tooling.


## Codex CLI Usage
- `nix run . -- --help`: run the packaged Codex CLI directly via the flake default app.
- `nix shell .#codex -c ./codex.sh -- --help`: invoke the wrapper that sources `env.sh` before launching Codex.
- `OPENAI_API_KEY` must be exported (or provided in `env.sh`); `OPENAI_BASE_URL` is optional for alternate endpoints.
