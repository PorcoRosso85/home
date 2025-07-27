{
  description = "URI POC E2E external tests";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    uri-poc = {
      url = "path:../..";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, uri-poc, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python311;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            python.pkgs.pytest
            python.pkgs.kuzu
            uri-poc.packages.${system}.default
          ];
        };
        
        packages.test = pkgs.writeScriptBin "test-uri-poc" ''
          #!${pkgs.bash}/bin/bash
          echo "Testing URI POC package..."
          ${python}/bin/python -m pytest test_package.py -v
        '';
      });
}