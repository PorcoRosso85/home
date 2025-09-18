# Demonstration of Git tracking limitation
# Tracked files later added to .gitignore are NOT excluded
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
  # This directory was tracked by Git, then added to .gitignore
  # Git's behavior: once tracked, .gitignore has no effect
  trackedThenIgnoredTest = {
    directoryName = "test-tracked-then-ignored";
    hasNixFile = true;  # Contains module.nix
    isInGitignore = true;  # Added to .gitignore after tracking
    
    # Expected: should still appear in missing (demonstrates Git limitation)
    appearsInMissing = builtins.elem "test-tracked-then-ignored" result.missingReadmes;
    
    # This demonstrates the limitation: Git won't exclude tracked files
    # even when they're later added to .gitignore
  };
  
  currentMissingDirs = result.missingReadmes;
  
  # This proves the limitation: Git tracking isn't a complete .gitignore parser
  # It's a "tracked file set" filter, which has different semantics
  limitationProven = builtins.elem "test-tracked-then-ignored" result.missingReadmes;
}