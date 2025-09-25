# SSOT Check: Nix-based verification for readme.nix ↔ README.md consistency
{ pkgs ? import <nixpkgs> {} }:

let
  # Load readme.nix data
  readmeData = import ./readme.nix;

  # SSOT verification script
  ssotCheck = pkgs.writeShellApplication {
    name = "ssot-check";
    runtimeInputs = with pkgs; [ nix ripgrep ];
    text = ''
      set -euo pipefail

      echo "🎯 Nix-based SSOT Verification"

      # Verify readme.nix can be imported
      if ! nix-instantiate --eval readme.nix >/dev/null 2>&1; then
        echo "❌ ERROR: readme.nix has syntax errors"
        exit 1
      fi

      # Check README.md exists
      if [[ ! -f README.md ]]; then
        echo "❌ ERROR: README.md not found"
        exit 1
      fi

      # Use ripgrep for efficient pattern matching
      echo "📋 Checking SSOT compliance patterns..."

      # Pattern 1: No exact description duplication
      README_DESC="${readmeData.description}"
      if rg -Fq "$README_DESC" README.md; then
        echo "❌ FAIL: Exact description duplication detected"
        exit 1
      fi

      # Pattern 2: No structured data patterns
      if rg -q "(goal|nonGoal|output|meta).*=" README.md; then
        echo "❌ FAIL: Structured data patterns found in README.md"
        rg "(goal|nonGoal|output|meta).*=" README.md
        exit 1
      fi

      # Pattern 3: readme.nix reference check
      if ! rg -qi "readme\.nix" README.md; then
        echo "⚠️  WARNING: README.md should reference readme.nix"
      fi

      echo "✅ SSOT compliance verified"
    '';
  };

in {
  inherit ssotCheck;

  # Provide the check as a standard derivation
  check = pkgs.runCommand "ssot-verification" {
    buildInputs = [ ssotCheck ];
  } ''
    cd ${./.}
    ssot-check
    touch $out
  '';

  meta = {
    description = "SSOT verification for readme.nix ↔ README.md consistency";
    version = readmeData.meta.version;
  };
}