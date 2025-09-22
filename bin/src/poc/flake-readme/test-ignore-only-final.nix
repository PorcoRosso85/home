# Final ignore-only policy validation test
let
  lib = (import <nixpkgs> {}).lib;
  flake-readme = import ./lib/core-docs.nix { inherit lib; self = { outPath = ./.; }; };

  # Get the actual directory structure
  rootContents = builtins.readDir ./.;
  allDirectories = lib.filterAttrs (name: type: type == "directory") rootContents;

  # Check which directories have readme.nix
  directoriesWithReadme = lib.filterAttrs (name: type:
    let dirContents = builtins.readDir (./. + "/${name}");
    in dirContents ? "readme.nix" && dirContents."readme.nix" == "regular"
  ) allDirectories;

  directoriesWithoutReadme = lib.filterAttrs (name: type:
    let dirContents = builtins.readDir (./. + "/${name}");
    in !(dirContents ? "readme.nix" && dirContents."readme.nix" == "regular")
  ) allDirectories;

  # Test with default ignore
  result = flake-readme.index { root = ./.; };

  # Expected missing: directories without readme.nix, minus those ignored by default
  expectedMissing = lib.filter (name:
    # Should be missing if: has no readme.nix AND not in default ignore list
    let hasNoReadme = directoriesWithoutReadme ? ${name};
        isInDefaultIgnore = builtins.elem name [".git" ".direnv" "node_modules" "result" "dist" "target" ".cache"] || name == "examples";
    in hasNoReadme && !isInDefaultIgnore
  ) (builtins.attrNames allDirectories);

in {
  ignoreOnlyPolicyValidation = {
    # Core policy test: ignore-only means ALL directories need readme.nix unless explicitly ignored
    policyCorrectlyApplied = {
      # Test 1: All directories without readme.nix should be flagged (except ignored ones)
      missingMatchesExpected = lib.sort builtins.lessThan result.missingReadmes == lib.sort builtins.lessThan expectedMissing;

      # Test 2: No directories with readme.nix should be flagged as missing
      noFalsePositives = lib.all (dir: !(builtins.elem dir result.missingReadmes)) (builtins.attrNames directoriesWithReadme);

      # Test 3: examples directory should be ignored (not in missing despite potentially lacking readme.nix)
      examplesIgnoredCorrectly = !(builtins.elem "examples" result.missingReadmes);

      # Test 4: Root directory should not be missing (has readme.nix)
      rootNotMissing = !(builtins.elem "." result.missingReadmes);
    };

    # Specific behavioral tests
    behaviorTests = {
      # Test 1: docs directory without readme.nix should be missing
      docsCorrectlyMissing = builtins.elem "docs" result.missingReadmes;

      # Test 2: lib directory with readme.nix should not be missing
      libCorrectlyPresent = !(builtins.elem "lib" result.missingReadmes);

      # Test 3: DEPRECATED_SPECS without readme.nix should be missing
      deprecatedCorrectlyMissing = builtins.elem "DEPRECATED_SPECS" result.missingReadmes;

      # Test 4: test directories without readme.nix should be missing
      testDirsCorrectlyMissing = lib.any (dir: lib.hasPrefix "test-" dir) result.missingReadmes;
    };

    # Detailed debug information
    detailedDebug = {
      allDirectories = builtins.attrNames allDirectories;
      directoriesWithReadme = builtins.attrNames directoriesWithReadme;
      directoriesWithoutReadme = builtins.attrNames directoriesWithoutReadme;
      expectedMissing = expectedMissing;
      actualMissing = result.missingReadmes;
      missingCount = builtins.length result.missingReadmes;
      expectedCount = builtins.length expectedMissing;
      rootHasReadme = rootContents ? "readme.nix";
      examplesInResults = builtins.elem "examples" result.missingReadmes;
    };
  };
}