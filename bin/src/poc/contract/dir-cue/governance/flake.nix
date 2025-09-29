{
  description = "Governance flake for CUE contract schema and checks distribution";

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
          ];
        };

        # Formatter
        formatter = pkgs.nixfmt;

        # Checks - CUE contract validation suite
        checks = {
          # Placeholder check that always succeeds
          governance-foundation = pkgs.runCommand "governance-foundation-check" {} ''
            echo "Governance foundation check passed"
            touch $out
          '';

          # CUE contract validation check
          cue-contracts = import ./checks/cue-check.nix {
            inherit pkgs;
            inherit (pkgs) lib stdenv cue findutils gawk;
          };
        };

        # Export check functions for consumer flakes
        lib = {
          # Main CUE contract check function for consumer import
          cueContractCheck = import ./checks/cue-check.nix;

          # Schema definitions for consumers
          schemas = {
            types = ./schema/types.cue;
          };
        };
      });
}