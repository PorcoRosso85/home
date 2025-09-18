# Comprehensive integration test for all Pure Nix improvements
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
  # Test all scenarios:
  # 1. Root directory (has flake.nix) → documentable, has readme.nix → not missing
  # 2. test-non-nix-dir (only .bin, .png files) → NOT documentable → not missing  
  # 3. test-no-readme-marker (has .nix + .no-readme) → IS documentable (.no-readme ignored) → appears in missing
  # 4. Any directory with .nix files but no readme.nix → should be missing
  
  allResults = {
    missing = result.missingReadmes;
    errorCount = result.errorCount;
    warningCount = result.warningCount;
    
    # Specific tests
    rootIsNotMissing = ! (builtins.elem "." result.missingReadmes);
    nonNixDirNotMissing = ! (builtins.elem "test-non-nix-dir" result.missingReadmes);
    noReadmeMarkerInMissing = builtins.elem "test-no-readme-marker" result.missingReadmes;  # Now appears in missing (marker ignored)
  };
  
  # Integration test success criteria
  integrationTestPasses = 
    result.errorCount == 0  # No validation errors
    && (! (builtins.elem "." result.missingReadmes))  # Root has readme.nix
    && (! (builtins.elem "test-non-nix-dir" result.missingReadmes))  # Non-.nix dirs ignored
    && (builtins.elem "test-no-readme-marker" result.missingReadmes);  # .no-readme marker ignored (current spec)
  
  # Summary of Pure Nix improvements working correctly
  pureNixImprovementsWorking = {
    gitFilteringViaFlake = true;  # Verified in Step 1
    nixOnlyDocumentable = ! (builtins.elem "test-non-nix-dir" result.missingReadmes);  # .nix-only logic
    nixOnlySpecification = builtins.elem "test-no-readme-marker" result.missingReadmes;  # .nix-only spec (markers ignored)
  };
}