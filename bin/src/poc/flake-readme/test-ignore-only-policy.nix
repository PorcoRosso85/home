# Test ignore-only policy implementation
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

  # Test defaultIgnore behavior by checking what's missing vs what exists
  allDirs = builtins.readDir ./.;
  examplesDirExists = allDirs ? "examples" && allDirs."examples" == "directory";

in {
  # Test ignore-only policy: ALL directories require readme.nix unless ignored
  ignoreOnlyPolicyTests = {
    # Test 1: Non-ignored directories without readme.nix should appear in missing
    nonIgnoredMustHaveReadme = builtins.length result.missingReadmes > 0;

    # Test 2: examples directory should NOT be in missing (it's ignored by default)
    examplesNotInMissing = examplesDirExists && !(builtins.elem "examples" result.missingReadmes);

    # Test 3: Root directory with readme.nix should NOT be missing
    rootNotMissing = ! (builtins.elem "." result.missingReadmes);

    # Test 4: lib directory should be in missing (it doesn't have readme.nix and isn't ignored)
    libDirInMissing = builtins.elem "lib" result.missingReadmes;

    # Test 5: No syntax errors in core evaluation
    noSyntaxErrors = result.errorCount == 0;

    # Test 6: Missing readmes list should contain actual directories
    hasActualMissingDirs = result.missingReadmes != [];

    # Test 7: Docs directory should be in missing if it exists and has no readme.nix
    docsDirHandledCorrectly =
      let docsExists = allDirs ? "docs" && allDirs."docs" == "directory";
      in if docsExists
         then builtins.elem "docs" result.missingReadmes
         else true; # pass if docs doesn't exist

    # Debug info
    debugInfo = {
      inherit (result) missingReadmes errorCount;
      examplesDirExists = examplesDirExists;
      availableDirs = builtins.attrNames (lib.filterAttrs (n: v: v == "directory") allDirs);
    };
  };
}