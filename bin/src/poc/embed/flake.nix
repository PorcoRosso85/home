{
  description = "Embedding and Similarity Search POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu_py.url = "path:../../persistence/kuzu_py";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu_py }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonPackages = pkgs.python311Packages;
        
        embedPoc = pythonPackages.buildPythonPackage {
          pname = "embed-poc";
          version = "0.1.0";
          src = ./.;
          
          propagatedBuildInputs = with pythonPackages; [
            pytest
            pytest-cov
            sentence-transformers
            torch
            transformers
            numpy
            kuzu_py.packages.${system}.default
          ];
          
          format = "pyproject";
          
          nativeBuildInputs = with pythonPackages; [
            setuptools
            wheel
          ];
        };
        
      in
      {
        packages = {
          default = embedPoc;
          inherit embedPoc;
        };
        
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test-embed-poc" ''
              export PYTHONPATH="${embedPoc}/${pythonPackages.python.sitePackages}:$PYTHONPATH"
              cd ${self}
              ${pythonPackages.python}/bin/python -m pytest test_embedding_repository.py -v
            ''}";
          };
          
          demo = {
            type = "app";
            program = "${pkgs.writeShellScript "demo-embed-poc" ''
              export PYTHONPATH="${embedPoc}/${pythonPackages.python.sitePackages}:$PYTHONPATH"
              cd ${self}
              ${pythonPackages.python}/bin/python demo_embedding_similarity.py
            ''}";
          };
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonPackages.python
            pythonPackages.pip
            pythonPackages.virtualenv
          ] ++ embedPoc.propagatedBuildInputs;
          
          shellHook = ''
            echo "Embedding and Similarity Search POC Development Shell"
            echo "Run 'nix run .#test' to run tests"
            echo "Run 'nix run .#demo' to run the demo"
          '';
        };
      });
}