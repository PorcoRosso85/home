{
  description = "Flake responsibility graph explorer - makes flake responsibilities searchable";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
    kuzu-py-flake.url = "path:/home/nixos/bin/src/persistence/kuzu_py";
    log-py-flake.url = "path:/home/nixos/bin/src/telemetry/log_py";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, kuzu-py-flake, log-py-flake }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            log-py-flake.overlays.default
          ];
        };
        
        # flake-graphパッケージをビルド
        flakeGraph = pkgs.python312Packages.buildPythonPackage rec {
          pname = "flake-graph";
          version = "0.1.0";
          pyproject = true;

          src = ./.;

          nativeBuildInputs = with pkgs.python312Packages; [
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pkgs.python312Packages; [
            kuzu-py-flake.packages.${system}.kuzuPy
            log_py
            pydantic
            pyyaml
            rich
            click
          ];

          checkInputs = with pkgs.python312Packages; [
            pytest
            pytest-json-report
          ];

          # テストは別途実行
          doCheck = false;
        };
        
        # Python環境を構築
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          flakeGraph
          pytest
          pytest-json-report
        ]);
      in
      {
        packages = {
          default = flakeGraph;
          flakeGraph = flakeGraph;
          pythonEnv = pythonEnv;
        };

        apps = {
          # Run tests
          test = {
            type = "app";
            program = toString (pkgs.writeShellScript "run-tests" ''
              ${pythonEnv}/bin/python -m pytest -xvs --import-mode=importlib
            '');
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            python-flake.packages.${system}.pyright
            python-flake.packages.${system}.ruff
          ];
          
          shellHook = ''
            echo "Flake Graph Explorer Development Environment"
            echo ""
            echo "Available tools:"
            echo "  - python with kuzu and log_py"
            echo "  - pyright (type checker)"
            echo "  - ruff (linter/formatter)"
            echo ""
            echo "Available commands:"
            echo "  nix run .#test      - Run tests"
          '';
        };
      });
}