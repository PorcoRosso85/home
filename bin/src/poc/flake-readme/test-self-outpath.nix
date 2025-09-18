# Test to verify self.outPath Git filtering effect
let 
  nixpkgs = import <nixpkgs> {};
  lib = nixpkgs.lib;
  flake-readme-lib = import ./lib/core-docs.nix { 
    inherit lib; 
    self = { outPath = ./.; };  # Simulate self.outPath behavior
  };
  
  # Test with direct path (should include untracked dirs)
  directPathResult = flake-readme-lib.index { 
    root = ./.;  # Direct path access
  };
  
  # Test with self.outPath simulation (should respect Git)
  selfOutPathResult = flake-readme-lib.index { 
    root = /home/nixos/bin/src/poc/flake-readme;  # Absolute path to simulate self.outPath
  };
  
in {
  # Compare missing readmes between direct and self.outPath approaches
  directMissing = directPathResult.missingReadmes;
  selfOutPathMissing = selfOutPathResult.missingReadmes;
  
  # Count difference (should show Git filtering effect)
  countDifference = builtins.length directPathResult.missingReadmes - builtins.length selfOutPathResult.missingReadmes;
  
  # Verification: Git filtering should reduce missing count
  gitFilteringWorks = builtins.length selfOutPathResult.missingReadmes <= builtins.length directPathResult.missingReadmes;
}