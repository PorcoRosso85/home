let 
  nixpkgs = import <nixpkgs> {};
  lib = nixpkgs.lib;
  flake-readme-lib = import ./lib/core-docs.nix { 
    inherit lib; 
    self = { outPath = ./test-fd-integration; }; 
  };
in
flake-readme-lib.index { 
  root = ./test-fd-integration;
  missingIgnoreExtra = name: type: false;  # Test fd-style logic
}