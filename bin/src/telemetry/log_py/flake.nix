{
  description = "Python implementation of universal log API";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      # Overlay that provides the log_py package
      overlay = final: prev: {
        pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
          (python-final: python-prev: {
            log_py = python-final.buildPythonPackage {
              pname = "log_py";
              version = "0.1.0";
              src = ./.;
              format = "pyproject";
              
              nativeBuildInputs = with python-final; [
                setuptools
                wheel
              ];
              
              propagatedBuildInputs = [];
              
              checkInputs = with python-final; [ 
                pytest 
              ];
              
              # Skip tests during build to avoid circular dependencies
              doCheck = false;
            };
          })
        ];
      };
    in
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlay ];
        };
        
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          log_py
          pytest
        ]);
      in
      {
        # Export the overlay for other flakes to use
        overlays.default = overlay;
        
        # Package outputs
        packages = {
          # The Python package itself
          default = pkgs.python3Packages.log_py;
          
          # Python environment with the package installed
          pythonEnv = pythonEnv;
          
          # Test runner package
          test = pkgs.writeShellScriptBin "test-log-py" ''
            set -e
            echo "=== Running log_py tests ==="
            cd ${self}
            export PYTHONPATH="${self}:$PYTHONPATH"
            # Run pytest with proper import mode
            ${pythonEnv}/bin/pytest tests/ -v --import-mode=importlib
          '';
        };
        
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            # Additional tools for development
            python3Packages.black
            python3Packages.pylint
            python3Packages.mypy
          ];
          
          shellHook = ''
            echo "log_py development environment"
            echo "Python with log_py module installed"
            echo "Run tests: nix run .#test"
          '';
        };
        
        # Apps
        apps = {
          # Run tests
          test = {
            type = "app";
            program = "${self.packages.${system}.test}/bin/test-log-py";
          };
          
          # Python REPL with log_py available
          repl = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "log-py-repl" ''
              echo "Starting Python REPL with log_py module..."
              ${pythonEnv}/bin/python
            ''}/bin/log-py-repl";
          };
          
          default = self.apps.${system}.test;
        };
      })
    # Export overlay at the flake level for easier consumption
    // {
      overlays.default = overlay;
    };
}