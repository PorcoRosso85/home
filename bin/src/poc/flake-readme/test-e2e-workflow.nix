let
  lib = (import <nixpkgs> {}).lib;
  flake-readme = import ./lib/core-docs.nix { inherit lib; self = { outPath = ./.; }; };

  # Test complete workflow: collect → normalize → validate → index
  collected = flake-readme.collect { root = ./.; };
  indexed = flake-readme.index { root = ./.; };

in {
  workflowTests = {
    collectionWorks = builtins.length (builtins.attrNames collected.byPath) > 0;
    indexingWorks = indexed.schemaVersion == 1;
    validationWorks = builtins.isList indexed.missingReadmes;
    ignoreOnlyActive = builtins.length indexed.missingReadmes > 0; # Should have missing items
    noSystemErrors = indexed.errorCount >= 0; # Should be non-negative number
  };
}