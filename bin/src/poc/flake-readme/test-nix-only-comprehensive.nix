# Test: ignore-only policy validation (NEW architectural specification)
# Purpose: Comprehensive validation that ALL directories require readme.nix unless explicitly ignored

let
  pkgs = import <nixpkgs> {};
  lib = pkgs.lib;
  
  # Load the current implementation
  coreDocs = import ./lib/core-docs.nix { inherit lib; self = ./.; };
  
  # Test data: mock directory structure to validate ignore-only policy
  testRoot = pkgs.runCommand "test-ignore-only-spec" {} ''
    mkdir -p $out
    
    # Directory with .nix file AND .no-readme marker - should require readme (marker ignored)
    mkdir -p $out/has-nix-with-marker
    echo "# some nix code" > $out/has-nix-with-marker/module.nix
    touch $out/has-nix-with-marker/.no-readme

    # Directory with .nix file but NO marker - should require readme
    mkdir -p $out/has-nix-no-marker
    echo "# some nix code" > $out/has-nix-no-marker/config.nix

    # Directory with only .no-readme marker, no .nix files - should require readme (NEW behavior)
    mkdir -p $out/only-marker-no-nix
    touch $out/only-marker-no-nix/.no-readme
    echo "not a nix file" > $out/only-marker-no-nix/readme.txt

    # Directory with no .nix files and no markers - should require readme (NEW behavior)
    mkdir -p $out/no-nix-no-marker
    echo "some text" > $out/no-nix-no-marker/file.txt

    # Directory with multiple .nix files - should require readme
    mkdir -p $out/multiple-nix-files
    echo "# config" > $out/multiple-nix-files/config.nix
    echo "# module" > $out/multiple-nix-files/module.nix
    touch $out/multiple-nix-files/.no-readme

    # Directory explicitly ignored (examples) - should NOT require readme
    mkdir -p $out/examples
    echo "sample code" > $out/examples/sample.nix
  '';
  
  # Get directory analysis and missing readmes list
  ignoreNothing = name: type: false;
  dirs = coreDocs._internal.listDirsRecursive {
    root = testRoot;
    ignore = ignoreNothing;
  };
  missingReadmes = coreDocs._internal.listMissingReadmes {
    root = testRoot;
    ignore = coreDocs.defaultIgnore;  # Use default ignore (includes examples/)
  };

  # Expected behavior for NEW ignore-only policy:
  # - ALL directories should require readme.nix unless explicitly ignored
  # - .no-readme markers are ignored (SRP: only ignore patterns matter)
  # - isDocumentable fact is preserved but not used in missing logic
  expectedMissingDirs = [
    "has-nix-with-marker"      # ALL dirs require readme (.no-readme ignored)
    "has-nix-no-marker"        # ALL dirs require readme
    "only-marker-no-nix"       # ALL dirs require readme (NEW behavior)
    "no-nix-no-marker"         # ALL dirs require readme (NEW behavior)
    "multiple-nix-files"       # ALL dirs require readme
    "."                        # Root dir also requires readme if not present
    # Note: examples/ should NOT appear (ignored by defaultIgnore)
  ];
  
  # Check missing readmes against expectations (NEW ignore-only policy)
  checkMissingResult = dir:
    let
      shouldBeMissing = builtins.elem dir expectedMissingDirs;
      actuallyMissing = builtins.elem dir missingReadmes;
    in
    if shouldBeMissing && actuallyMissing
    then "✓ ${dir}: correctly missing (ignore-only policy)"
    else if !shouldBeMissing && !actuallyMissing
    then "✓ ${dir}: correctly not missing"
    else if shouldBeMissing && !actuallyMissing
    then "✗ ${dir}: expected missing but not in list"
    else "✗ ${dir}: unexpectedly missing";

  # Test all directories we created
  testDirs = [ "has-nix-with-marker" "has-nix-no-marker" "only-marker-no-nix"
               "no-nix-no-marker" "multiple-nix-files" "." ];
  results = map checkMissingResult testDirs;

  # Special check: examples/ should NOT be missing (ignored)
  examplesNotMissing = ! (builtins.elem "examples" missingReadmes);
  examplesResult = if examplesNotMissing
    then "✓ examples: correctly ignored (not missing)"
    else "✗ examples: should be ignored but appears in missing list";

  allResults = results ++ [ examplesResult ];
  allPassed = lib.all (r: lib.hasPrefix "✓" r) allResults;
  passedCount = builtins.length (lib.filter (r: lib.hasPrefix "✓" r) allResults);
  totalCount = builtins.length allResults;
  
in {
  inherit testRoot dirs missingReadmes allResults;

  # Validation results
  testResult = if allPassed
    then "PASS: All directories correctly handled according to ignore-only policy"
    else "FAIL: Some directories not handled correctly";

  # New policy validation
  policyCompliance = if allPassed
    then "✓ Current implementation fully complies with ignore-only policy"
    else "✗ Current implementation has issues with ignore-only policy";

  # Summary statistics
  testScore = "${builtins.toString passedCount}/${builtins.toString totalCount} tests passed";

  # Representative cases verification
  representativeCases = {
    # Case 1: non-.nix directory now requires readme (NEW behavior)
    nonNixDirRequiresReadme = builtins.elem "no-nix-no-marker" missingReadmes;
    # Case 2: .nix directory still requires readme
    nixDirRequiresReadme = builtins.elem "has-nix-no-marker" missingReadmes;
    # Case 3: ignored directory (examples/) excluded from requirements
    ignoredDirExcluded = ! (builtins.elem "examples" missingReadmes);
    # Case 4: .no-readme markers are ignored (markers don't affect policy)
    noReadmeMarkersIgnored = builtins.elem "has-nix-with-marker" missingReadmes;
    # Case 5: root directory treated consistently
    rootDirConsistent = builtins.elem "." missingReadmes;  # root requires readme if not present
  };

  summary = "Test validates ignore-only policy: ALL directories require readme.nix unless explicitly ignored (architectural change from .nix-only)";
}