{
  description = "Local Sync Engine POC";

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
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
          ];

          shellHook = ''
            echo "Local Sync Engine - TDD Development Environment"
            echo "Commands:"
            echo "  deno task test       - Run all tests"
            echo "  deno task test:watch - Run tests in watch mode"
          '';
        };
      });
}