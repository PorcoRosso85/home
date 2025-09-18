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
        
        # Build embed package
        embedPkg = pythonPackages.buildPythonPackage {
          pname = "embed-pkg";
          version = "0.1.0";
          src = ./.;
          
          propagatedBuildInputs = with pythonPackages; [
            # Core dependencies only
            pyarrow
            kuzuPyPackage
          ];
          
          passthru.optional-dependencies = {
            ml = with pythonPackages; [
              sentence-transformers
              torch
              transformers
              numpy
            ];
          };
          
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
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "embed-default" ''
              echo "Available apps:"
              echo "  nix run .#test              - Run all tests"
              echo "  nix run .#test-external     - Run external E2E tests only"
              echo "  nix run .#demo              - Run standalone demo"
              echo "  nix run .#readme            - Show README"
            ''}";
          };
          
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              ${pkgs.bat}/bin/bat README.md || ${pkgs.coreutils}/bin/cat README.md
            ''}";
          };
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test-embed-poc" ''
              # Run all tests in the current directory
              export PYTHONPATH="$PWD:$PYTHONPATH"
              
              # Unit tests
              echo "Running unit tests..."
              ${python.withPackages (ps: [embedPkg ps.pytest ps.pytest-cov])}/bin/pytest test_*.py -v
              
              # Internal E2E tests
              if [ -d "e2e/internal" ]; then
                echo ""
                echo "Running internal E2E tests..."
                ${python.withPackages (ps: [embedPkg ps.pytest ps.pytest-cov])}/bin/pytest e2e/internal/ -v
              else
                echo "⚠️  WARNING: No internal E2E tests found"
              fi
              
              # External E2E tests
              if [ -f "e2e/external/test_package.py" ]; then
                echo ""
                echo "Running external E2E tests..."
                ${python.withPackages (ps: [embedPkg ps.pytest])}/bin/pytest e2e/external/test_package.py -v
              else
                echo "⚠️  WARNING: No external E2E tests found"
              fi
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
              # Run standalone demo in the current directory
              export PYTHONPATH="$PWD:$PYTHONPATH"
              exec ${python.withPackages (ps: [embedPkg])}/bin/python demo_standalone_embedding.py
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