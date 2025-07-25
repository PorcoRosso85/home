{
  description = "S3 client abstraction library";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          boto3
          pytest
          pytest-asyncio
          moto
        ]);
      in
      {
        packages.default = pkgs.python3Packages.buildPythonPackage {
          pname = "s3-client";
          version = "0.1.0";
          src = ./.;
          
          propagatedBuildInputs = with pkgs.python3Packages; [
            boto3
          ];
          
          pythonImportsCheck = [ "s3_client" ];
          
          # Disable tests during build to avoid circular dependency
          doCheck = false;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];
          
          shellHook = ''
            echo "S3 Client Development Environment"
            echo "Available commands:"
            echo "  nix run .#test  - Run tests"
          '';
        };

        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "run-tests" ''
            export PYTHONPATH="${./.}:$PYTHONPATH"
            exec ${pythonEnv}/bin/pytest s3_client/ -v
          ''}";
        };
      });
}