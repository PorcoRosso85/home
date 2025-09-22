let
  lib = (import <nixpkgs> {}).lib;
  flake-readme = import ./lib/core-docs.nix { inherit lib; self = { outPath = ./.; }; };

  startTime = builtins.currentTime;
  result = flake-readme.index { root = ./.; };
  endTime = builtins.currentTime;

in {
  performanceMetrics = {
    executionTimeUnder1s = (endTime - startTime) < 1;
    missingCount = builtins.length result.missingReadmes;
    errorCount = result.errorCount;
    warningCount = result.warningCount;
    docsFound = builtins.length (builtins.attrNames result.docs);
  };
}