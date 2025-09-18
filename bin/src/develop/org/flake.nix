{
  description = "Org project - Python 3.12 environment with libtmux and testing";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python 3.12 with required packages
        python = pkgs.python312;
        pythonPackages = pkgs.python312Packages;
        
        pythonEnv = python.withPackages (ps: [
          ps.libtmux
          ps.pytest
          ps.pytest-cov
          ps.pytest-mock
        ]);

      in
      {
        # Development shell - compatible with nix shell
        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            pythonPackages.libtmux
            pythonPackages.pytest
            pythonPackages.pytest-cov
            pythonPackages.pytest-mock
          ];
          
          shellHook = ''
            echo "Python 3.12 development environment for org project"
            echo "Available: libtmux, pytest, pytest-cov, pytest-mock"
            echo "Run tests with: nix run .#test"
            export PYTHONPATH="$PWD:$PYTHONPATH"
          '';
        };

        # Test runner app
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "run-tests" ''
              set -e
              export PYTHONPATH="$PWD:$PYTHONPATH"
              ${pythonEnv}/bin/pytest "$@"
            ''}";
          };
          
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "run-tests" ''
              set -e
              export PYTHONPATH="$PWD:$PYTHONPATH"
              ${pythonEnv}/bin/pytest "$@"
            ''}";
          };
        };

        # Package for the org project
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "org";
          version = "0.1.0";
          src = ./.;
          
          buildInputs = [ pythonEnv ];
          
          installPhase = ''
            mkdir -p $out
            cp -r . $out/
          '';
        };
      });
}