{
  description = "Deno + Kuzu-wasm development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            nodejs_20
          ];

          shellHook = ''
            echo "Deno + Kuzu-wasm environment"
            echo "Commands:"
            echo "  deno test src/   - Run tests"
            echo "  npm i kuzu-wasm   - Install kuzu-wasm"
          '';
        };
      });
}