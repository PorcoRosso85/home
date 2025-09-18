{
  description = "Meta Node POC - Cypherクエリをノードに格納して動的実行するPOC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-py.url = "path:../../persistence/kuzu_py";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-py, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python環境
        pythonEnv = pkgs.python312.withPackages (ps: [
          ps.pytest
          ps.kuzu
          ps.numpy
        ]);

        # テストスクリプト
        testScript = pkgs.writeShellScriptBin "test" ''
          echo "Running Meta Node POC tests..."
          export PYTHONPATH="$PWD:$PYTHONPATH"
          ${pythonEnv}/bin/pytest -v tests/
        '';
      in
      {
        packages = {
          default = testScript;
          test = testScript;
        };

        apps = {
          test = {
            type = "app";
            program = "${testScript}/bin/test";
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
          ];
          
          shellHook = ''
            echo "Meta Node POC開発環境"
            echo "Python環境とKuzuDBが利用可能です"
          '';
        };
      });
}