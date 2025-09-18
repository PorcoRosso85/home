{
  description = "Architecture analysis and design tool for cross-project responsibility separation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    # Inherit from parent Python environment
    python-flake = {
      url = "path:../flakes/python";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    
    # For semantic analysis of project descriptions
    # This includes kuzu-py as a dependency
    vss-kuzu = {
      url = "path:../search/vss_kuzu";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    
    # Migration tool for KuzuDB
    kuzu-migration = {
      url = "path:../poc/kuzu_migration";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, vss-kuzu, kuzu-migration }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        python = pkgs.python312;
        
        pythonPackages = pkgs.python312Packages;
        
        architectureTool = pythonPackages.buildPythonApplication {
          pname = "architecture-tool";
          version = "0.1.0";
          
          src = ./.;
          
          pyproject = true;
          
          build-system = with pythonPackages; [
            setuptools
          ];
          
          propagatedBuildInputs = with pythonPackages; [
            # Get kuzu from vss-kuzu's dependency to avoid conflicts
            vss-kuzu.packages.${system}.vssKuzu
            
            # Additional dependencies
            pydantic
            typer
            rich
            networkx
            matplotlib
          ];
          
          doCheck = false;
        };
      in
      {
        packages = {
          default = architectureTool;
          pythonEnv = python.withPackages (ps: architectureTool.propagatedBuildInputs);
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            (python.withPackages (ps: architectureTool.propagatedBuildInputs ++ (with ps; [
              pytest
              pytest-asyncio
              pytest-cov
              black
              ruff
              mypy
              ipython
            ])))
            kuzu-migration.packages.${system}.default
          ];
          
          shellHook = ''
            echo "Architecture Analysis Tool Development Environment"
            echo "Purpose: Cross-project responsibility separation and design"
            echo ""
            echo "Commands:"
            echo "  pytest        - Run tests"
            echo "  black .       - Format code"
            echo "  ruff check .  - Lint code"
            echo "  mypy .        - Type check"
          '';
        };
        
        apps = {
          default = {
            type = "app";
            program = "${architectureTool}/bin/architecture";
          };
          
          test = {
            type = "app";
            program = let
              testEnv = python.withPackages (ps: architectureTool.propagatedBuildInputs ++ (with ps; [
                pytest
                pytest-asyncio
              ]));
            in "${pkgs.writeShellScript "test" ''
              set -e
              echo "=== Running Architecture Tool Tests ==="
              cd ${./.}
              
              # Infrastructure tests
              if [ -f test_infrastructure_spec.py ]; then
                echo "Running infrastructure tests..."
                ${testEnv}/bin/pytest -v test_infrastructure_spec.py
              fi
              
              # DDL specification tests
              if [ -d ddl ] && ls ddl/test_*.py 2>/dev/null; then
                echo "Running DDL tests..."
                ${testEnv}/bin/pytest -v ddl/test_*.py
              fi
              
              # DQL specification tests
              if [ -d dql ] && ls dql/test_*.py 2>/dev/null; then
                echo "Running DQL tests..."
                ${testEnv}/bin/pytest -v dql/test_*.py
              fi
              
              # Integration tests
              if ls test_integration_*.py 2>/dev/null; then
                echo "Running integration tests..."
                ${testEnv}/bin/pytest -v test_integration_*.py
              fi
              
              # E2E tests
              if [ -d "e2e/internal" ]; then
                echo "Running E2E tests..."
                ${testEnv}/bin/pytest -v e2e/internal/
              fi
              
              echo "=== All tests completed ==="
            ''}";
          };
        };
      });
}