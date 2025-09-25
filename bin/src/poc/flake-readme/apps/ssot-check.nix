# SSOT Check App: Standalone application for SSOT verification
{ pkgs }:

pkgs.writeShellApplication {
  name = "ssot-check";
  runtimeInputs = with pkgs; [ nix ripgrep ];
  text = ''
    set -euo pipefail

    echo "🎯 SSOT Verification: readme.nix ↔ README.md consistency"

    # Verify we're in a project directory
    if [[ ! -f readme.nix ]]; then
        echo "❌ ERROR: readme.nix not found in current directory"
        echo "Run this command from a project root containing readme.nix"
        exit 1
    fi

    if [[ ! -f README.md ]]; then
        echo "❌ ERROR: README.md not found in current directory"
        exit 1
    fi

    # Check 1: readme.nix can be evaluated
    if ! nix-instantiate --eval readme.nix --attr description >/dev/null 2>&1; then
        echo "❌ ERROR: readme.nix has evaluation errors"
        exit 1
    fi

    # Check 2: No exact description duplication
    README_DESC=$(nix-instantiate --eval --strict readme.nix --attr description | tr -d '"')
    if rg -Fq "$README_DESC" README.md; then
        echo "❌ ERROR: README.md contains exact duplicate of readme.nix description"
        echo "Found: $README_DESC"
        echo "Fix: Use natural language variation instead of exact copying"
        exit 1
    fi

    # Check 3: No structured data patterns in README.md
    if rg -q "(goal|nonGoal|output|meta).*=" README.md; then
        echo "❌ ERROR: README.md contains structured data patterns"
        echo "These belong in readme.nix, not README.md:"
        rg "(goal|nonGoal|output|meta).*=" README.md || true
        echo "Fix: Move structured data to readme.nix, keep narrative in README.md"
        exit 1
    fi

    # Check 4: readme.nix reference (warning only)
    if ! rg -qi "readme\.nix" README.md; then
        echo "⚠️  SUGGESTION: README.md could reference readme.nix for detailed specs"
        echo "   Example: 'See readme.nix for technical specifications'"
    fi

    echo "✅ SSOT verification passed - good separation between structured and narrative docs"
  '';
}