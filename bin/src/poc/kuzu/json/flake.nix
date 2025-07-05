{
  description = "KuzuDB JSON POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          kuzu
          pytest
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            ruff
          ];

          shellHook = ''
            echo "KuzuDB JSON POC environment"
            echo "Python 3.11 with kuzu, pytest, and ruff available"
          '';
        };

        apps = {
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "run-kuzu-json" ''
              ${pythonEnv}/bin/python ${self}/kuzu_json_poc/__init__.py
            ''}";
          };

          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test-kuzu-json" ''
              ${pythonEnv}/bin/pytest ${self}/test_*.py -v
            ''}";
          };
        };
      });
}