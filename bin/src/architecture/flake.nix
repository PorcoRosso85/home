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
    
    # Graph database for architecture knowledge
    kuzu-py = {
      url = "path:../persistence/kuzu_py";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    
    # For semantic analysis of project descriptions
    vss-kuzu = {
      url = "path:../search/vss_kuzu";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, kuzu-py, vss-kuzu }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = python-flake.packages.${system}.pythonEnv;
        
        pythonPackages = python.pkgs;
        
        architectureTool = pythonPackages.buildPythonApplication {
          pname = "architecture-tool";
          version = "0.1.0";
          
          src = ./.;
          
          propagatedBuildInputs = with pythonPackages; [
            # Inherit dependencies
            kuzu-py.packages.${system}.default
            vss-kuzu.packages.${system}.default
            
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
        
        apps.default = {
          type = "app";
          program = "${architectureTool}/bin/architecture";
        };
      });
}