# Test: .nix-only documentable determination (validates current specification)
# Purpose: Comprehensive validation that .nix file presence determines documentability

let
  pkgs = import <nixpkgs> {};
  lib = pkgs.lib;
  
  # Load the current implementation
  coreDocs = import ./lib/core-docs.nix { inherit lib; self = ./.; };
  
  # Test data: mock directory structure to validate .nix-only determination
  testRoot = pkgs.runCommand "test-nix-only-spec" {} ''
    mkdir -p $out
    
    # Directory with .nix file AND .no-readme marker - should be documentable (marker ignored)
    mkdir -p $out/has-nix-with-marker
    echo "# some nix code" > $out/has-nix-with-marker/module.nix
    touch $out/has-nix-with-marker/.no-readme
    
    # Directory with .nix file but NO marker - should be documentable  
    mkdir -p $out/has-nix-no-marker
    echo "# some nix code" > $out/has-nix-no-marker/config.nix
    
    # Directory with only .no-readme marker, no .nix files - should NOT be documentable
    mkdir -p $out/only-marker-no-nix
    touch $out/only-marker-no-nix/.no-readme
    echo "not a nix file" > $out/only-marker-no-nix/readme.txt
    
    # Directory with no .nix files and no markers - should NOT be documentable
    mkdir -p $out/no-nix-no-marker
    echo "some text" > $out/no-nix-no-marker/file.txt
    
    # Additional test: multiple .nix files - should be documentable
    mkdir -p $out/multiple-nix-files
    echo "# config" > $out/multiple-nix-files/config.nix
    echo "# module" > $out/multiple-nix-files/module.nix
    touch $out/multiple-nix-files/.no-readme
  '';
  
  # Get directory analysis
  ignoreNothing = name: type: false;
  dirs = coreDocs._internal.listDirsRecursive { 
    root = testRoot; 
    ignore = ignoreNothing; 
  };
  
  # Expected behavior for .nix-only specification:
  # - Directories with .nix files should ALWAYS be documentable (markers ignored)
  # - Directories without .nix files should NEVER be documentable (regardless of markers)
  expectedResults = {
    "has-nix-with-marker" = { hasReadme = false; isDocumentable = true; };   # .no-readme ignored
    "has-nix-no-marker" = { hasReadme = false; isDocumentable = true; };      # has .nix
    "only-marker-no-nix" = { hasReadme = false; isDocumentable = false; };   # no .nix files
    "no-nix-no-marker" = { hasReadme = false; isDocumentable = false; };     # no .nix files
    "multiple-nix-files" = { hasReadme = false; isDocumentable = true; };    # multiple .nix files
  };
  
  # Check results
  checkResult = path: expected:
    let actual = dirs.${path}; in
    if actual.isDocumentable == expected.isDocumentable
    then "✓ ${path}: documentable=${builtins.toString expected.isDocumentable}"
    else "✗ ${path}: expected documentable=${builtins.toString expected.isDocumentable}, got ${builtins.toString actual.isDocumentable}";
  
  results = lib.mapAttrsToList checkResult expectedResults;
  
  # All tests should pass with current .nix-only specification
  allPassed = lib.all (r: lib.hasPrefix "✓" r) results;
  passedCount = builtins.length (lib.filter (r: lib.hasPrefix "✓" r) results);
  totalCount = builtins.length results;
  
in {
  inherit testRoot dirs expectedResults results;
  
  # Validation results
  testResult = if allPassed
    then "PASS: All directories correctly classified according to .nix-only specification"
    else "FAIL: Some directories not classified correctly";
    
  # Current implementation validation
  specificationCompliance = if allPassed
    then "✓ Current implementation fully complies with .nix-only specification"
    else "✗ Current implementation has issues with .nix-only specification";
    
  # Summary statistics
  testScore = "${builtins.toString passedCount}/${builtins.toString totalCount} tests passed";
  
  summary = "Test validates .nix-only spec: directories are documentable iff they contain .nix files (excluding readme.nix)";
}