# Test ignoreExtra functionality with ignore-only policy
let
  lib = (import <nixpkgs> {}).lib;
  flake-readme = import ./lib/core-docs.nix { inherit lib; self = { outPath = ./.; }; };

  # Test with custom ignore function
  testWithExtra = flake-readme.index {
    root = ./.;
    missingIgnoreExtra = (name: type: builtins.elem name ["docs" "test-no-readme-marker"]);
  };

  # Test without extra ignore
  testWithoutExtra = flake-readme.index {
    root = ./.;
  };

  # Test with overlapping ignore (examples is already in defaultIgnore)
  testWithOverlap = flake-readme.index {
    root = ./.;
    missingIgnoreExtra = (name: type: builtins.elem name ["examples" "docs"]);
  };

in {
  ignoreExtraTests = {
    # Test 1: missingIgnoreExtra should reduce missing readmes count
    extraIgnoreReducesMissing =
      (builtins.length testWithExtra.missingReadmes) < (builtins.length testWithoutExtra.missingReadmes);

    # Test 2: docs should not be in missing when ignored via missingIgnoreExtra
    docsNotInMissingWhenIgnored = !(builtins.elem "docs" testWithExtra.missingReadmes);

    # Test 3: docs should be in missing when not ignored
    docsInMissingWhenNotIgnored = builtins.elem "docs" testWithoutExtra.missingReadmes;

    # Test 4: test-no-readme-marker should not be in missing when ignored
    testDirNotInMissingWhenIgnored = !(builtins.elem "test-no-readme-marker" testWithExtra.missingReadmes);

    # Test 5: overlapping ignore should work (examples ignored by both default and extra)
    overlappingIgnoreWorks = !(builtins.elem "examples" testWithOverlap.missingReadmes);

    # Test 6: DEPRECATED_SPECS should still be missing (not in extra ignore)
    deprecatedStillMissing = builtins.elem "DEPRECATED_SPECS" testWithExtra.missingReadmes;

    # Debug information
    debugInfo = {
      withExtra = testWithExtra.missingReadmes;
      withoutExtra = testWithoutExtra.missingReadmes;
      withOverlap = testWithOverlap.missingReadmes;
      extraCount = builtins.length testWithExtra.missingReadmes;
      normalCount = builtins.length testWithoutExtra.missingReadmes;
    };
  };
}