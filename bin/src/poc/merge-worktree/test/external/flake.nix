{
  description = "External usage example for worktree-limiter";

  inputs = {
    worktree-limiter.url = "path:../..";
    nixpkgs.follows = "worktree-limiter/nixpkgs";
    flake-utils.follows = "worktree-limiter/flake-utils";
  };

  outputs = { self, worktree-limiter, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        # Must Fix: name argument for custom binary name
        packages.custom-limiter = worktree-limiter.lib.${system}.makeWorktreeLimiter {
          name = "custom-limiter";  # Custom binary name
          coreRefs = [ "refs/heads/main" "refs/heads/staging" ];
          allowedGlobs = [ "services/*/**" "shared/**" ];
          allowInitialCreate = true;
          allowOutsideDelete = false;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            self.packages.${system}.custom-limiter
            worktree-limiter.packages.${system}.testEnv
          ];
          shellHook = ''
            echo "Custom worktree limiter environment"
            echo "Binary: custom-limiter"
            echo "Core refs: main, staging"
            echo "Allowed: services/**, shared/**"
          '';
        };

        # External configuration test (Must Fix: binary name consistency)
        checks.config-test = pkgs.runCommand "config-test" {
          buildInputs = [ self.packages.${system}.custom-limiter ];
        } ''
          set -euo pipefail

          # Custom name execution confirmation
          which custom-limiter

          # Custom configuration --help confirmation (Must Fix: custom name display)
          custom-limiter --help | grep -q "custom-limiter"
          custom-limiter --help | grep -q "staging"
          custom-limiter --help | grep -q "services"

          echo "Custom configuration verified"
          touch $out
        '';

        # Integration test
        checks.integration-test = pkgs.runCommand "integration-test" {
          buildInputs = [
            self.packages.${system}.custom-limiter
            worktree-limiter.packages.${system}.testEnv
          ];
        } ''
          set -euo pipefail
          export PATH=${worktree-limiter.packages.${system}.testEnv}/bin:$PATH

          # Binary existence confirmation
          which custom-limiter
          which bats

          # Configuration confirmation
          custom-limiter --help

          echo "Integration test completed"
          touch $out
        '';

        apps.test-custom = {
          type = "app";
          program = "${pkgs.writeShellScript "test-custom" ''
            set -euo pipefail

            echo "Testing custom limiter configuration..."

            # Binary name confirmation
            echo "Binary available: $(which custom-limiter)"

            # Configuration content confirmation (Must Fix: custom name in help)
            echo "Configuration:"
            custom-limiter --help

            # Custom name properly displayed in help
            if custom-limiter --help | grep -q "custom-limiter"; then
              echo "✅ Custom name properly displayed in help"
            else
              echo "❌ Custom name not found in help"
              exit 1
            fi

            echo "Custom limiter test completed successfully"
          ''}";
        };
      });
}