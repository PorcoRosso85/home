# Repository Guidelines

## Project Structure & Module Organization
- Root contains `flake.nix` (tooling and tasks). Blog content lives as Markdown files in this folder. 
- Place images under `images/` and reference them with relative paths (`./images/...`).
- Optional helpers (scripts or data) can live in `tools/` and `data/` respectively when needed.

## Build, Test, and Development Commands
- `nix develop` — enter a dev shell with project tools (if provided by the flake). Use this before editing.
- `nix flake check` — run flake-defined checks (format, lint, or eval). Keep green before pushing.
- `nix build` — build artifacts defined by the flake. Outputs to `./result`.
- `nix run` — run the default app/preview if defined (useful for local preview).

## Coding Style & Naming Conventions
- Markdown: wrap at ~100 chars, use descriptive headings, and add language tags to code fences (e.g., ```bash).
- Filenames: `YYYY-MM-DD-slug.md` for posts; images `images/slug-01.png`.
- Links: prefer relative links within this folder; verify they resolve.
- Nix: 2-space indentation, double quotes for strings, alphabetical attribute order where practical.

## Testing Guidelines
- Primary check: `nix flake check` must pass.
- Content quality: run a Markdown linter if available in the dev shell; ensure code blocks are copy-pasteable.
- Links and images: verify locally; avoid external dead links. For large assets, use compressed PNG/JPEG/WebP.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.
- Commits should be small and focused. Include context in the body when non-trivial.
- PRs must include: scope/summary, before/after screenshots for visual changes, and confirmation that `nix flake check` passes.
- Link related issues and note any follow-ups.

## Security & Configuration Tips
- Do not commit secrets, tokens, or `.env` files. Redact API keys in examples.
- Prefer local relative assets; avoid hotlinking third-party images.

## Agent-Specific Instructions
- Keep changes minimal and surgical; do not rename files or restructure without justification.
- Follow the conventions above; prefer adding new files over large rewrites.
- If a command is undefined in the flake, state the assumption in the PR and provide a fallback.
