# Test: ignore-only policy validation (validates NEW specification)
# Purpose: Verify that ALL directories require readme.nix unless explicitly ignored
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
  # Missing readmes under NEW ignore-only policy
  currentMissing = result.missingReadmes;

  # NEW policy validation:
  # - test-no-readme-marker: should be missing (ALL dirs require readme)
  # - test-non-nix-dir: should be missing (NEW behavior - non-.nix dirs now require readme)
  # - root ".": should NOT be missing (has readme.nix)

  # Test case 1: Directory with .nix file + .no-readme marker
  nixDirWithMarkerMissing = builtins.elem "test-no-readme-marker" result.missingReadmes;

  # Test case 2: Directory with NO .nix files (NEW requirement)
  nonNixDirMissing = builtins.elem "test-non-nix-dir" result.missingReadmes;

  # Test case 3: Root directory with readme.nix
  rootNotMissing = ! (builtins.elem "." result.missingReadmes);

  # All tests should pass with NEW ignore-only policy
  testPasses = nixDirWithMarkerMissing && nonNixDirMissing && rootNotMissing;

  # Validation: files exist as expected
  markerFileExists = builtins.pathExists ./test-no-readme-marker/.no-readme;
  nixFileExists = builtins.pathExists ./test-no-readme-marker/module.nix;
  nonNixDirExists = builtins.pathExists ./test-non-nix-dir;

  # Representative cases for new policy
  representativeCases = {
    # Case 1: .nix directory still requires readme (consistent)
    nixDirRequiresReadme = nixDirWithMarkerMissing;
    # Case 2: non-.nix directory now requires readme (NEW behavior)
    nonNixDirRequiresReadme = nonNixDirMissing;
    # Case 3: .no-readme markers are ignored
    markersIgnored = nixDirWithMarkerMissing && markerFileExists;
    # Case 4: root with readme.nix not missing
    rootWithReadmeNotMissing = rootNotMissing;
  };

  summary = "Test confirms ignore-only policy: ALL directories require readme.nix unless explicitly ignored (architectural change from .nix-only)";
}