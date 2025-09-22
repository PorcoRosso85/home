# Test for ignore-only policy (NEW architectural change)
let
  nixpkgs = import <nixpkgs> {};
  lib = nixpkgs.lib;
  flake-readme-lib = import ./lib/core-docs.nix {
    inherit lib;
    self = { outPath = ./.; };
  };

  # Test with actual test directories in current repo
  result = flake-readme-lib.index {
    root = ./.;
  };

in {
  # Current missing readmes under new ignore-only policy
  currentMissing = result.missingReadmes;

  # NEW ignore-only policy: ALL directories require readme.nix unless explicitly ignored
  # In current repo:
  # - test-non-nix-dir: has only .bin/.png files → SHOULD require documentation (NEW behavior)
  # - test-no-readme-marker: has .nix file + .no-readme → SHOULD require documentation (.no-readme ignored)
  # - root ".": has flake.nix + readme.nix → should NOT be missing (has readme.nix)

  expectedBehavior = {
    # Under NEW ignore-only policy, these should appear in missing list
    shouldBeMissing = [ "test-non-nix-dir" "test-no-readme-marker" ];
    # Root has readme.nix, so should not be missing
    shouldNotBeMissing = [ "." ];
  };
  
  # Verification of new ignore-only logic
  ignoreOnlyLogicWorks =
    (builtins.elem "test-non-nix-dir" result.missingReadmes) &&  # non-.nix dir now requires readme
    (builtins.elem "test-no-readme-marker" result.missingReadmes) &&  # .no-readme markers ignored
    (! (builtins.elem "." result.missingReadmes));  # root has readme.nix

  # Representative test cases for new policy
  representativeCases = {
    nonNixDirRequiresReadme = builtins.elem "test-non-nix-dir" result.missingReadmes;  # NEW: now required
    nixDirRequiresReadme = builtins.elem "test-no-readme-marker" result.missingReadmes;  # Still required
    rootWithReadmeNotMissing = ! (builtins.elem "." result.missingReadmes);  # Has readme.nix
  };

  # Summary of architectural change
  architecturalChange = {
    old = "Only directories with .nix files required documentation (isDocumentable-based)";
    new = "All directories require readme.nix unless explicitly ignored (ignore-only policy)";
    impact = "test-non-nix-dir now appears in missing list (behavior change)";
  };
}