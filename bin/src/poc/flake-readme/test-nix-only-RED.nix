# GREEN Test: Should PASS with NEW ignore-only implementation
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

  # With NEW ignore-only logic: test-non-nix-dir has NO .nix files
  # but ALL directories require readme.nix unless explicitly ignored
  hasNonNixDirInMissing = builtins.elem "test-non-nix-dir" result.missingReadmes;

  # This test should PASS (return true) with NEW implementation
  # because ignore-only policy requires ALL directories to have readme.nix
  ignoreOnlyLogicImplemented = builtins.elem "test-non-nix-dir" result.missingReadmes;

  # Expected: true (GREEN state) - ignore-only policy working
  testPasses = builtins.elem "test-non-nix-dir" result.missingReadmes;

  # Verification that architectural change is working
  architecturalChangeVerified = {
    before = "Only .nix directories required readme.nix";
    after = "ALL directories require readme.nix unless ignored";
    evidence = "test-non-nix-dir now appears in missing list";
    success = hasNonNixDirInMissing;
  };
}