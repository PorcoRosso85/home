{
  description = "Embedding and Similarity Search POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
    kuzu_py.url = "path:../../persistence/kuzu_py";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, kuzu_py }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = python-flake.packages.${system}.pythonEnv;
        python = pythonEnv.python;
        pythonPackages = python.pkgs;
        
        # Build kuzu_py package
        kuzuPyPackage = kuzu_py.packages.${system}.default;
        
        # Build asvs_reference package
        asvsReference = pythonPackages.buildPythonPackage {
          pname = "asvs-reference";
          version = "0.1.0";
          src = ../asvs_reference;
          
          propagatedBuildInputs = with pythonPackages; [
            pyyaml
            jinja2
            kuzuPyPackage
          ];
          
          format = "pyproject";
          
          nativeBuildInputs = with pythonPackages; [
            setuptools
            wheel
          ];
          
          # Disable conflict check due to pythonEnv dependencies
          catchConflicts = false;
        };
        
        # Build embed package
        embedPkg = pythonPackages.buildPythonPackage {
          pname = "embed-pkg";
          version = "0.1.0";
          src = ./.;
          
          propagatedBuildInputs = with pythonPackages; [
            asvsReference
            sentence-transformers
            torch
            transformers
            numpy
            kuzuPyPackage
          ];
          
          format = "pyproject";
          
          nativeBuildInputs = with pythonPackages; [
            setuptools
            wheel
          ];
          
          # Disable conflict check due to pythonEnv dependencies
          catchConflicts = false;
        };
        
      in
      {
        packages = {
          default = embedPkg;
          inherit embedPkg;
        };
        
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test-embed-poc" ''
              # Run tests in the current directory
              export PYTHONPATH="$PWD:$PWD/../asvs_reference:$PYTHONPATH"
              exec ${python.withPackages (ps: [embedPkg ps.pytest ps.pytest-cov])}/bin/pytest test_embedding_repository.py -v
            ''}";
          };
          
          test-external = {
            type = "app";
            program = "${pkgs.writeShellScript "test-external" ''
              cd ${self}/e2e/external
              exec ${python.withPackages (ps: [embedPkg ps.pytest])}/bin/pytest test_package.py -v
            ''}";
          };
          
          demo = {
            type = "app";
            program = "${pkgs.writeShellScript "demo-embed-poc" ''
              # Run demo in the current directory
              # Add both current directory and asvs_reference to PYTHONPATH
              export PYTHONPATH="$PWD:$(dirname $PWD)/asvs_reference:$PYTHONPATH"
              exec ${python.withPackages (ps: [embedPkg asvsReference])}/bin/python embed_pkg/demo_embedding_similarity.py
            ''}";
          };
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            (python.withPackages (ps: with ps; [
              embedPkg
              pytest
              pytest-cov
              ipython
              black
              isort
              mypy
              flake8
            ]))
          ];
          
          shellHook = ''
            echo "Embedding and Similarity Search POC Development Shell"
            echo ""
            echo "Available commands:"
            echo "  nix run .#test              - Run unit tests"
            echo "  nix run .#test-external     - Run external E2E tests"
            echo "  nix run .#demo              - Run the demo"
            echo ""
            echo "Python environment with embed_pkg and all dependencies available"
          '';
        };
      });
}