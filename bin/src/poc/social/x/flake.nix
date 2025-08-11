{
  description = "X.com Developer API POC - Bun TypeScript Implementation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    bun-flake.url = "path:../../../flakes/bun";
    bun-flake.inputs.nixpkgs.follows = "nixpkgs";
    bun-flake.inputs.flake-utils.follows = "flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, bun-flake }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        bunDevEnv = bun-flake.packages.${system}.default;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            bunDevEnv
            pkgs.curl
            pkgs.jq
          ];

          shellHook = ''
            echo "X.com Developer API POC - Bun TypeScript Environment"
            echo "Available tools: bun, tsc, typescript-language-server, biome"
            echo "Use 'bun init' to initialize project if not already done"
          '';
        };

        packages.default = pkgs.writeScriptBin "x-api-poc" ''
          #!${pkgs.bash}/bin/bash
          if [ $# -eq 0 ]; then
            echo "X.com Developer API POC - TypeScript Implementation"
            echo "Usage: nix run . <tweet_id>"
            echo "Example: nix run . 1234567890123456789"
            exit 1
          fi
          
          cd ${./.}
          export PATH=${bunDevEnv}/bin:$PATH
          bun run src/cli.ts "$@"
        '';
      });
}