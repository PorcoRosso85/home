{
  description = "Pyright test with nixpkgs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pyrightTest = pkgs.writeShellScriptBin "pyright-test" ''
          #!${pkgs.bash}/bin/bash
          echo "Testing pyright from nixpkgs..."
          echo "Version:"
          ${pkgs.nodePackages.pyright}/bin/pyright --version
          echo ""
          echo "Running on test_good.py:"
          ${pkgs.nodePackages.pyright}/bin/pyright test_good.py
        '';
        
      in
      {
        packages = {
          default = pyrightTest;
        };
      }
    );
}