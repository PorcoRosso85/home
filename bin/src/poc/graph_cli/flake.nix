{
  description = "Graph CLI - Display KuzuDB query results in CUI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-ts-persistence.url = "path:../../persistence/kuzu_ts";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts-persistence }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        graph-cli = pkgs.writeShellScriptBin "graph-cli" ''
          export DENO_DIR="$(mktemp -d)"
          export DENO_IMPORT_MAP="${self}/import_map.json"
          export KUZU_TS_PATH="${kuzu-ts-persistence.lib.importPath}"
          ${pkgs.deno}/bin/deno run \
            --allow-read \
            --allow-write \
            --allow-env \
            --allow-ffi \
            --unstable-ffi \
            --no-lock \
            ${self}/main.ts "$@"
          rm -rf "$DENO_DIR"
        '';
      in
      {
        packages = {
          default = graph-cli;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
          ];
          
          shellHook = ''
            export DENO_IMPORT_MAP="${self}/import_map.json"
            export KUZU_TS_PATH="${kuzu-ts-persistence.lib.importPath}"
            echo "Graph CLI development environment"
            echo "Run 'deno task dev' to start development"
          '';
        };
      });
}