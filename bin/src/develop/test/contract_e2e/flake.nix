{
  description = "Contract-based E2E testing framework using JSON Schema";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        python = pkgs.python311;
        pythonPackages = python.pkgs;
        
        # Define our Python package
        contract-e2e = pythonPackages.buildPythonPackage {
          pname = "contract-e2e";
          version = "0.1.0";
          src = ./.;
          
          propagatedBuildInputs = with pythonPackages; [
            jsonschema
            hypothesis
          ];
          
          checkInputs = with pythonPackages; [
            pytest
            pytest-cov
          ];
          
          # Ensure tests are discovered from src/
          checkPhase = ''
            pytest src/
          '';
        };
      in
      {
        packages = {
          default = contract-e2e;
          contract-e2e = contract-e2e;
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            pythonPackages.pytest
            pythonPackages.pytest-cov
            pythonPackages.jsonschema
            pythonPackages.hypothesis
            pythonPackages.black
            pythonPackages.isort
            pythonPackages.flake8
            pythonPackages.mypy
          ];
          
          shellHook = ''
            echo "Contract E2E Testing Framework Development Shell"
            echo "Run 'pytest' to execute tests"
          '';
        };
        
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "run-tests" ''
              ${python}/bin/python -m pytest src/ -v
            ''}";
          };
        };
        
        lib = {
          # This will be implemented as we build the framework
          mkContractE2ETest = { name, executable, inputSchema, outputSchema }: 
            throw "mkContractE2ETest not yet implemented";
        };
      });
}