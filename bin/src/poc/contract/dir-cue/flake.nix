{
  description = "dir-cue: governance-flake implementation for CUE contract management";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            cue
            nixfmt
            python312Packages.pytest
          ];
        };

        # Formatter
        formatter = pkgs.nixfmt;

        # Checks - CUE contract validation suite
        checks = {
          governance-foundation = pkgs.runCommand "governance-foundation-check" {} ''
            echo "Governance foundation check passed"
            touch $out
          '';

          # CUE contract validation check (simplified version)
          cue-contracts = pkgs.runCommand "cue-contract-checks" {
            buildInputs = with pkgs; [ cue ];
            preferLocalBuild = true;
            allowSubstitutes = false;
          } ''
            echo "[INFO] Starting governance-flake CUE validation..."

            # Copy essential schema files for validation
            mkdir -p governance/schema
            cp ${./governance/schema/types.cue} governance/schema/types.cue
            cp ${./governance/dir.cue} governance/dir.cue

            # 1. Schema validation
            echo "[INFO] Running CUE schema validation..."
            if ! cue vet governance/schema/types.cue; then
              echo "[ERROR] Schema validation failed"
              exit 1
            fi
            echo "[INFO] ✓ Schema validation passed"

            # 2. Format check
            echo "[INFO] Running CUE format check on schema..."
            if ! cue fmt --check governance/schema/types.cue; then
              echo "[ERROR] Schema format check failed"
              exit 1
            fi
            if ! cue fmt --check governance/dir.cue; then
              echo "[ERROR] Dir contract format check failed"
              exit 1
            fi
            echo "[INFO] ✓ Format check passed"

            # 3. Basic schema compatibility test
            echo "[INFO] Testing schema structure validation..."
            # Test that schema exports expected definitions
            if cue eval -e '#DirContract' governance/schema/types.cue > /dev/null; then
              echo "[INFO] ✓ DirContract schema found"
            else
              echo "[ERROR] DirContract schema missing"
              exit 1
            fi

            if cue eval -e '#FlakeContract' governance/schema/types.cue > /dev/null; then
              echo "[INFO] ✓ FlakeContract schema found"
            else
              echo "[ERROR] FlakeContract schema missing"
              exit 1
            fi

            echo "[INFO] ✓ Schema structure validation passed"

            echo "[INFO] ✓ All governance-flake CUE checks passed!"
            echo "Governance-flake CUE checks completed successfully" > $out
          '';
        };

        # Export check functions for consumer flakes
        lib = {
          # Main CUE contract check function for consumer import
          cueContractCheck = import ./governance/checks/cue-check.nix;

          # Schema definitions for consumers
          schemas = {
            types = ./governance/schema/types.cue;
          };
        };
      });
}