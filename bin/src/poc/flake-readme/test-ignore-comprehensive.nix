# Comprehensive ignore-only policy test suite
let
  lib = (import <nixpkgs> {}).lib;
  flake-readme = import ./lib/core-docs.nix { inherit lib; self = { outPath = ./.; }; };

  # Test default behavior
  defaultTest = flake-readme.index { root = ./.; };

  # Test with custom ignore function that ignores everything
  ignoreAllTest = flake-readme.index {
    root = ./.;
    ignore = (name: type: true);
  };

  # Test with no ignore function (should use defaultIgnore)
  noIgnoreTest = flake-readme.index {
    root = ./.;
    ignore = null;
  };

  # Test missingIgnoreExtra only (keep default collect ignore)
  missingOnlyTest = flake-readme.index {
    root = ./.;
    missingIgnoreExtra = (name: type: name == "lib" || name == "docs");
  };

  # Test specific directory behavior
  allDirs = builtins.readDir ./.;

in {
  comprehensiveIgnoreTests = {
    # Policy verification tests
    ignoreOnlyPolicyEnforced = {
      # Test 1: Default ignore excludes examples but includes other dirs without readme.nix
      examplesExcludedByDefault = !(builtins.elem "examples" defaultTest.missingReadmes);

      # Test 2: lib directory missing readme.nix should be detected
      libMissingDetected = builtins.elem "lib" defaultTest.missingReadmes;

      # Test 3: Root directory with readme.nix should not be missing
      rootHasReadme = !(builtins.elem "." defaultTest.missingReadmes);

      # Test 4: All directories ignored should result in empty missing list
      ignoreAllResultsEmpty = ignoreAllTest.missingReadmes == [];
    };

    # missingIgnoreExtra functionality tests
    missingIgnoreExtraWorks = {
      # Test 1: lib excluded via missingIgnoreExtra should not be missing
      libExcludedViaMissingExtra = !(builtins.elem "lib" missingOnlyTest.missingReadmes);

      # Test 2: docs excluded via missingIgnoreExtra should not be missing
      docsExcludedViaMissingExtra = !(builtins.elem "docs" missingOnlyTest.missingReadmes);

      # Test 3: DEPRECATED_SPECS should still be missing (not in missingIgnoreExtra)
      deprecatedStillMissing = builtins.elem "DEPRECATED_SPECS" missingOnlyTest.missingReadmes;

      # Test 4: examples should still be excluded (via defaultIgnore)
      examplesStillExcluded = !(builtins.elem "examples" missingOnlyTest.missingReadmes);
    };

    # Edge cases and validation
    edgeCaseTests = {
      # Test 1: null ignore should behave same as defaultIgnore
      nullIgnoreSameAsDefault = defaultTest.missingReadmes == noIgnoreTest.missingReadmes;

      # Test 2: Error count should be reasonable (some missing readmes expected)
      reasonableErrorCount = defaultTest.errorCount >= builtins.length defaultTest.missingReadmes;

      # Test 3: Missing readmes should be actual directories
      missingAreDirectories = lib.all (path:
        let dirName = if path == "." then "." else builtins.baseNameOf path;
        in allDirs ? ${dirName} && allDirs.${dirName} == "directory"
      ) defaultTest.missingReadmes;

      # Test 4: No duplicate entries in missing readmes
      noDuplicatesInMissing =
        let unique = lib.unique defaultTest.missingReadmes;
        in builtins.length unique == builtins.length defaultTest.missingReadmes;
    };

    # Debug information for troubleshooting
    debugInfo = {
      defaultMissing = defaultTest.missingReadmes;
      defaultErrorCount = defaultTest.errorCount;
      missingOnlyMissing = missingOnlyTest.missingReadmes;
      availableDirectories = builtins.attrNames (lib.filterAttrs (n: v: v == "directory") allDirs);
      hasReadmeNix = allDirs ? "readme.nix";
      rootReadmeExists = (builtins.readDir ./.) ? "readme.nix";
    };
  };
}