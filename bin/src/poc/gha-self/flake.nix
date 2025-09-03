{
  description = "GitHub Actions self-hosted runner POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # GitHub Actions self-hosted runner
            github-runner
            
            # GitHub CLI for token generation
            gh
            
            # Required tools
            git
            curl
            jq
            docker
            
            # Shell utilities
            bash
            coreutils
          ];

          shellHook = ''
            echo "GitHub Actions self-hosted runner POC environment"
            echo "================================================"
            echo ""
            echo "Available commands:"
            echo "  ./register-runner.sh - Register runner with GitHub"
            echo "  ./run-runner.sh      - Start the runner"
            echo ""
            echo "Quick start:"
            echo "  1. nix develop"
            echo "  2. ./register-runner.sh"
            echo "  3. ./run-runner.sh"
            echo ""
          '';
        };
      });
}