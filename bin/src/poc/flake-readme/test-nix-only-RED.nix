# RED Test: Should FAIL with current implementation
let 
  nixpkgs = import <nixpkgs> {};
  lib = nixpkgs.lib;
  flake-readme-lib = import ./lib/core-docs.nix { 
    inherit lib; 
    self = { outPath = ./.; };
  };
  
  result = flake-readme-lib.index { 
    root = ./.;
  };
  
in {
  # Current missing readmes (should include test-non-nix-dir)
  currentMissing = result.missingReadmes;
  
  # With current logic: test-non-nix-dir has regular files (data.bin, image.png)
  # so it's considered documentable and appears in missing list
  hasNonNixDirInMissing = builtins.elem "test-non-nix-dir" result.missingReadmes;
  
  # This test should FAIL (return false) with current implementation
  # because .nix-only logic is not yet implemented
  nixOnlyLogicImplemented = ! (builtins.elem "test-non-nix-dir" result.missingReadmes);
  
  # Expected: false (RED state) - same as nixOnlyLogicImplemented
  testPasses = ! (builtins.elem "test-non-nix-dir" result.missingReadmes);
}