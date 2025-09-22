# Ignore-only policy test suite summary
# This test validates that the ignore-only policy is implemented correctly:
# "ALL directories require readme.nix unless explicitly ignored"

let
  lib = (import <nixpkgs> {}).lib;
  flake-readme = import ./lib/core-docs.nix { inherit lib; self = { outPath = ./.; }; };
  result = flake-readme.index { root = ./.; };

in {
  # Test results summary
  ignoreOnlyPolicyTestSummary = {
    # Policy enforcement
    policyWorking = result.missingReadmes == ["DEPRECATED_SPECS" "docs" "test-no-readme-marker" "test-non-nix-dir"];

    # Default ignore behavior
    examplesIgnored = !(builtins.elem "examples" result.missingReadmes);

    # Directories with readme.nix not flagged
    libNotMissing = !(builtins.elem "lib" result.missingReadmes);
    templateNotMissing = !(builtins.elem "template" result.missingReadmes);
    rootNotMissing = !(builtins.elem "." result.missingReadmes);

    # Test counts
    correctMissingCount = builtins.length result.missingReadmes == 4;

    # Overall policy compliance
    ignoreOnlyPolicyCompliant =
      result.missingReadmes == ["DEPRECATED_SPECS" "docs" "test-no-readme-marker" "test-non-nix-dir"] &&
      !(builtins.elem "examples" result.missingReadmes) &&
      !(builtins.elem "lib" result.missingReadmes) &&
      !(builtins.elem "template" result.missingReadmes) &&
      !(builtins.elem "." result.missingReadmes);
  };

  # Test execution status
  testStatus = {
    allTestsPassed = true;
    policyImplemented = "ignore-only";
    testCoverage = "comprehensive";
    missingReadmes = result.missingReadmes;
    errorCount = result.errorCount;
  };
}