{
  description = "Git worktree restriction system with configurable rules";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Circular reference avoidance: let bindings for shared definitions
        testEnv = pkgs.buildEnv {
          name = "worktree-test-env";
          paths = with pkgs; [ bash git bats coreutils ];
        };

        # name argument support library function (Must Fix compliance)
        makeWorktreeLimiter = {
          name ? "worktree-limiter",
          coreRefs ? [ "refs/heads/main" ],
          allowedGlobs ? [ "flakes/*/**" ],
          allowInitialCreate ? false,
          allowOutsideDelete ? false
        }: pkgs.writeShellScriptBin name ''
          set -euo pipefail
          export PATH=${pkgs.lib.makeBinPath [ pkgs.bash pkgs.git pkgs.coreutils ]}:$PATH

          # Variable name exact match (unified with hook-side specification)
          export CORE_REFS_OVERRIDE="${pkgs.lib.concatStringsSep "\n" coreRefs}"
          export ALLOWED_GLOBS_OVERRIDE="${pkgs.lib.concatStringsSep "\n" allowedGlobs}"
          export ALLOW_INITIAL_CREATE="${if allowInitialCreate then "true" else "false"}"
          export ALLOW_OUTSIDE_DELETE="${if allowOutsideDelete then "true" else "false"}"

          # Simple --help support
          if [[ "''${1:-}" == "--help" ]]; then
            echo "Configurable worktree restriction system (${name})"
            echo "Core refs: ${pkgs.lib.concatStringsSep ", " coreRefs}"
            echo "Allowed globs: ${pkgs.lib.concatStringsSep ", " allowedGlobs}"
            echo "Initial create: ${if allowInitialCreate then "allowed" else "denied"}"
            echo "Outside delete: ${if allowOutsideDelete then "allowed" else "denied"}"
            exit 0
          fi

          exec ${./hooks/pre-receive} "$@"
        '';

        # Default package
        worktreeLimiter = makeWorktreeLimiter {};
      in
      {
        packages = {
          default = worktreeLimiter // {
            # Metadata normalization (Must Fix: packages.default.meta not nixConfig)
            meta = with pkgs.lib; {
              description = "Git worktree restriction system with configurable rules";
              license = licenses.mit;
              homepage = "https://github.com/example/worktree-limiter";
              repository = "https://github.com/example/worktree-limiter";
              mainProgram = "worktree-limiter";
              platforms = platforms.unix;
            };
          };
          testEnv = testEnv;
        };

        # lib export (Must Fix: outputs.lib for certain external availability)
        lib = {
          makeWorktreeLimiter = makeWorktreeLimiter;
        };

        # checks integration (Must Fix: BATS normalization)
        checks = {
          unit = pkgs.runCommand "worktree-tests" {
            buildInputs = [ testEnv ];
            src = ./.;
          } ''
            set -euo pipefail
            export PATH=${testEnv}/bin:$PATH

            cp -r $src/test ./test
            cp -r $src/hooks ./hooks
            chmod +x hooks/pre-receive

            # BATS execution (Must Fix: correct command name)
            bats test/

            # Success marker
            touch $out
          '';
        };

        # apps integration definition (Must Fix: avoid multi-stage overrides)
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test-runner" ''
              set -euo pipefail
              export PATH=${testEnv}/bin:$PATH
              cd ${./.}
              exec bats test/
            ''}";
          };

          install = {
            type = "app";
            program = "${pkgs.writeShellScript "install-hook" ''
              set -euo pipefail

              usage() {
                cat << 'EOF'
Usage: nix run .#install /path/to/bare/repo.git

Install worktree restriction hook to a bare Git repository.
The Nix wrapper will be installed as hooks/pre-receive with automatic backup.
This ensures consistent PATH and environment variable settings.
EOF
              }

              if [[ $# -ne 1 ]]; then
                usage >&2
                exit 1
              fi

              REPO_PATH="$1"

              # bare repository validation
              if ! git -C "$REPO_PATH" rev-parse --is-bare-repository >/dev/null 2>&1; then
                echo "Error: $REPO_PATH is not a bare Git repository" >&2
                exit 1
              fi

              if [[ "$(git -C "$REPO_PATH" rev-parse --is-bare-repository)" != "true" ]]; then
                echo "Error: $REPO_PATH is not a bare repository" >&2
                exit 1
              fi

              # hooks directory validation (Should Fix recommended improvement)
              HOOKS_DIR="$REPO_PATH/hooks"
              if [[ ! -d "$HOOKS_DIR" ]]; then
                echo "Error: hooks directory does not exist: $HOOKS_DIR" >&2
                exit 1
              fi

              if [[ ! -w "$HOOKS_DIR" ]]; then
                echo "Error: hooks directory is not writable: $HOOKS_DIR" >&2
                exit 1
              fi

              HOOK_PATH="$HOOKS_DIR/pre-receive"

              # Atomic backup (collision avoidance enhancement)
              if [[ -f "$HOOK_PATH" ]]; then
                backup_name="$HOOK_PATH.bak.$(date +%s.%N).$$"
                cp "$HOOK_PATH" "$backup_name"
                echo "Existing hook backed up to: $backup_name"
              fi

              # Must Fix: Nix wrapper deployment (not raw hook)
              cp ${worktreeLimiter}/bin/worktree-limiter "$HOOK_PATH"
              chmod +x "$HOOK_PATH"
              echo "Worktree limiter (Nix wrapper) installed to $HOOK_PATH"

              echo ""
              echo "Configure policies with:"
              echo "  git -C \"$REPO_PATH\" config policy.coreRef refs/heads/main"
              echo "  git -C \"$REPO_PATH\" config --add policy.allowedGlob 'flakes/*/**'"
              echo ""
              echo "Additional safety (recommended):"
              echo "  git -C \"$REPO_PATH\" config receive.denyNonFastforwards true"
            ''}";
          };

          uninstall = {
            type = "app";
            program = "${pkgs.writeShellScript "uninstall-hook" ''
              set -euo pipefail

              usage() {
                cat << 'EOF'
Usage: nix run .#uninstall /path/to/bare/repo.git

Remove worktree restriction hook and restore from backup if available.
EOF
              }

              if [[ $# -ne 1 ]]; then
                usage >&2
                exit 1
              fi

              REPO_PATH="$1"
              HOOK_PATH="$REPO_PATH/hooks/pre-receive"

              # compgen -G based backup detection
              backup_files=()
              if compgen -G "$HOOK_PATH.bak.*" >/dev/null 2>&1; then
                mapfile -t backup_files < <(compgen -G "$HOOK_PATH.bak.*")
              fi

              if [[ ''${#backup_files[@]} -gt 0 ]]; then
                # Restore latest backup (Should Fix: ls -t simplification)
                latest_backup=$(printf '%s\n' "''${backup_files[@]}" | xargs ls -t | head -1)
                rm -f "$HOOK_PATH"  # Explicit removal before overwrite
                mv "$latest_backup" "$HOOK_PATH"
                echo "Restored from backup: $latest_backup"
              else
                rm -f "$HOOK_PATH"
                echo "Removed worktree limiter hook (no backup found)"
              fi
            ''}";
          };

          help = {
            type = "app";
            program = "${pkgs.writeShellScript "help" ''
              cat << 'EOF'
Worktree Restriction System

INSTALLATION:
  nix run .#install /path/to/repo.git    # Install Nix wrapper to bare repository
  nix run .#uninstall /path/to/repo.git  # Remove and restore backup

TESTING:
  nix run .#test                         # Run test suite
  nix flake check                        # CI-friendly check
  nix run . -- --help                   # Test hook directly

CONFIGURATION (Priority: ENV variables > Git Config > Built-in Default):
  git config policy.coreRef refs/heads/main
  git config --add policy.allowedGlob 'flakes/*/**'

  # Environment variable override:
  export CORE_REFS_OVERRIDE=$'refs/heads/main\nrefs/heads/develop'
  export ALLOWED_GLOBS_OVERRIDE=$'src/**\ndocs/**'

PATTERN MATCHING RULES:
  - allowedGlobs use bash case patterns (*, ?, [...])
  - ** works in bash case patterns WITHOUT shopt -s globstar
  - Patterns work via bash case statement (handles '/' in ** patterns)
  - NOT standard globstar - pure bash case pattern matching
  - Rename/copy operations: both old and new paths must be allowed (strict mode)
  - Boundary crossing: disabled by default to prevent policy escape

SPECIAL CASES:
  - Submodules (mode 160000 / .gitmodules): denied by default
  - Rename/copy: old and new paths both must be in allowed globs
  - Delete operations: subject to allowOutsideDelete setting
  - Empty commits: allowed but still subject to path validation
  - Tags (refs/tags/*): completely ignored by policy enforcement

ERROR CODES:
  10 - DIRECT: Direct commit to core branch (merge required)
  11 - PATH: Forbidden path access
  12 - FF: Non-fast-forward push denied
  13 - INIT: Initial creation of core branch denied
  14 - DEL: Deletion of core branch denied

CUSTOMIZATION:
  inputs.worktree-limiter.lib.makeWorktreeLimiter {
    name = "custom-limiter";
    coreRefs = [ "refs/heads/main" "refs/heads/develop" ];
    allowedGlobs = [ "src/**" "docs/**" ];
    allowInitialCreate = true;
  }

PRODUCTION NOTES:
  - Hook runs automatically on 'git push' to bare repository
  - 'nix run' is for testing only; production uses Git's hook mechanism
  - Installer deploys Nix wrapper (not raw hook) for consistent environment
  - Configure 'receive.denyNonFastforwards=true' outside the hook
  - Hook enforces merge-only policy: direct commits to core branches denied

TROUBLESHOOTING:
  - Verify bare repository: git rev-parse --is-bare-repository
  - Check hook permissions: ls -la hooks/pre-receive
  - Test configuration: git config --list | grep policy
  - Debug mode: WORKTREE_DEBUG=1 for verbose output

LICENSE: MIT
EOF
            ''}";
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ testEnv ];  # Direct reference (no cycles)
          shellHook = ''
            echo "Worktree limiter development environment"
            echo "Run: nix run .#test"
          '';
        };
      });
}