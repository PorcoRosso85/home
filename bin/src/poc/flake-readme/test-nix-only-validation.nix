# Test: .nix-only documentable determination (validates current specification)
# Purpose: Verify that directories with .nix files are considered documentable regardless of markers
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
  # Current missing readmes
  currentMissing = result.missingReadmes;
  
  # test-no-readme-marker has module.nix (.nix file exists)
  # Current spec: directories with .nix files are ALWAYS documentable (markers ignored)
  hasMarkerDirInMissing = builtins.elem "test-no-readme-marker" result.missingReadmes;
  
  # With current implementation: .no-readme markers are completely ignored
  # test-no-readme-marker should appear in missing list because it has .nix file but no readme.nix
  nixOnlyBehaviorConfirmed = builtins.elem "test-no-readme-marker" result.missingReadmes;
  
  # Expected: true (confirms .nix-only specification)
  testPasses = builtins.elem "test-no-readme-marker" result.missingReadmes;
  
  # Validation: marker file exists but is ignored (as expected)
  markerFileExists = builtins.pathExists ./test-no-readme-marker/.no-readme;
  nixFileExists = builtins.pathExists ./test-no-readme-marker/module.nix;
  
  summary = "Test confirms .nix-only specification: directories with .nix files are documentable regardless of .no-readme markers";
}