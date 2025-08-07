{
  description = "Email send POC - Send emails from storage or drafts";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    bun.url = "path:../../../flakes/bun";
  };

  outputs = { self, nixpkgs, flake-utils, bun }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        bunPkg = bun.packages.${system}.default;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            bunPkg
            # AWS CLI for SES testing
            awscli2
          ];

          shellHook = ''
            echo "Email Send Service - Bun Development Environment"
            echo "Bun version: $(bun --version)"
            echo ""
            echo "Available commands:"
            echo "  bun install    - Install dependencies"
            echo "  bun run dev    - Run development server"
            echo "  bun test       - Run tests"
            echo ""
          '';
        };
      });
}