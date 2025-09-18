# Test for .nix-only documentable judgment
let 
  nixpkgs = import <nixpkgs> {};
  lib = nixpkgs.lib;
  flake-readme-lib = import ./lib/core-docs.nix { 
    inherit lib; 
    self = { outPath = ./.; };
  };
  
  # Test current behavior vs expected behavior with .nix-only logic
  result = flake-readme-lib.index { 
    root = ./test-fd-integration;
  };
  
in {
  # Current missing readmes
  currentMissing = result.missingReadmes;
  
  # Expected behavior: non-.nix directories should not be considered documentable
  # In test-fd-integration:
  # - ignored-dir: has test.txt (not .nix) → should NOT be documentable
  # - normal-dir: has test.txt (not .nix) → should NOT be documentable  
  # - root: has .gitignore, flake.nix, readme.nix → should be documentable (has .nix files)
  
  # This test should FAIL with current implementation
  # Expected: ignored-dir and normal-dir should not be in missing list
  expectedBehavior = {
    shouldNotBeMissing = [ "test-fd-integration/ignored-dir" "test-fd-integration/normal-dir" ];
    shouldRemainDocumentable = [ "test-fd-integration" ];  # has flake.nix
  };
  
  # Verification (should fail with current logic)
  nixOnlyLogicWorks = ! (lib.any (dir: builtins.elem dir result.missingReadmes) 
    [ "test-fd-integration/ignored-dir" "test-fd-integration/normal-dir" ]);
}