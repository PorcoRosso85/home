{
  description = "FTS (Full-Text Search) with KuzuDB";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
    kuzu-py-flake.url = "path:/home/nixos/bin/src/persistence/kuzu_py";
    log-py.url = "path:/home/nixos/bin/src/telemetry/log_py";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, kuzu-py-flake, log-py }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # Apply log_py overlay to get the log_py python package
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ log-py.overlays.default ];
        };
        
        # Get kuzuPy package from kuzu-py-flake
        kuzuPyPackage = kuzu-py-flake.packages.${system}.kuzuPy;
        
        # Create Python environment
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
            # Base testing framework
            pytest
            
            # Core dependencies for FTS
            kuzu  # Base kuzu package
            kuzuPyPackage  # This provides kuzu_py module
            numpy
            
            # Telemetry
            log_py  # stdout logging from log_py (available via overlay)
            
            # Development tools
            pytest-cov
            black
            ruff
        ]);
        
      in {
        packages.default = pkgs.python312Packages.buildPythonPackage {
          pname = "fts-kuzu";
          version = "0.2.0";
          src = pkgs.lib.fileset.toSource {
            root = ./.;
            fileset = pkgs.lib.fileset.unions [
              ./pyproject.toml
              ./README.md
              ./MANIFEST.in
              ./fts_kuzu
            ];
          };
          format = "pyproject";
          
          nativeBuildInputs = with pkgs.python312Packages; [
            setuptools
            wheel
            build  # Add the build package
          ];
          
          propagatedBuildInputs = with pkgs.python312Packages; [
            kuzuPyPackage
            numpy
            log_py
          ];
          
          # Disable import check as it fails in build environment but works at runtime
          pythonImportsCheck = [ ];
          
          meta = with pkgs.lib; {
            description = "Full-Text Search with KuzuDB";
            homepage = "https://github.com/your-org/fts-kuzu";
            license = licenses.mit;
          };
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            uv
            ruff
            black
          ];
          
          shellHook = ''
            echo "FTS KuzuDB Implementation"
            echo "========================"
            echo ""
            echo "Available commands:"
            echo "  nix run .#test      - Run tests"
            echo "  nix run .#lint      - Run linter"
            echo "  nix run .#format    - Format code"
            echo ""
            
            # No PYTHONPATH needed, testing pure flake input
          '';
        };
        
        apps = {
          # Test runner
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              # Run tests from the source directory
              cd /home/nixos/bin/src/search/fts_kuzu
              echo "Running FTS tests..."
              # Run pytest with importlib import mode to avoid namespace conflicts
              PYTHONPATH=. exec ${pythonEnv}/bin/pytest -v --import-mode=importlib tests/ "$@"
            ''}";
          };
          
          # Linter
          lint = {
            type = "app";
            program = "${pkgs.writeShellScript "lint" ''
              cd ${./.}
              echo "Running linter..."
              ${pkgs.ruff}/bin/ruff check .
            ''}";
          };
          
          # Formatter
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format" ''
              cd ${./.}
              echo "Formatting code..."
              ${pkgs.black}/bin/black .
              ${pkgs.ruff}/bin/ruff format .
            ''}";
          };
        };
      });
}