# CUE contract check function for consumer flakes
# Usage: governance-flake.lib.cueContractCheck { src = ./.; pkgs = nixpkgs.legacyPackages.x86_64-linux; }

{ src, pkgs, ... }:

pkgs.runCommand "cue-contract-validation" {
  buildInputs = with pkgs; [ cue ];
  preferLocalBuild = true;
  allowSubstitutes = false;
} ''
  echo "[INFO] Starting CUE contract validation for consumer project..."

  # Copy source for pure evaluation
  cp -r ${src} source
  cd source

  # Check for required contract files
  contract_errors=()

  # 1. Check for dir.cue (if it's a project root)
  if [[ -f "flake.nix" && ! -f "dir.cue" ]]; then
    contract_errors+=("Missing dir.cue contract file")
  fi

  # 2. Check for contracts/flake.cue (if it's a flake directory)
  if [[ -f "flake.nix" && ! -f "contracts/flake.cue" ]]; then
    contract_errors+=("Missing contracts/flake.cue contract file")
  fi

  # 3. Format validation for existing CUE files
  if find . -name "*.cue" -type f | head -1 | read; then
    echo "[INFO] Validating CUE file formats..."
    for cue_file in $(find . -name "*.cue" -type f); do
      echo "[INFO] Checking format of $cue_file"
      if ! cue fmt --check "$cue_file"; then
        contract_errors+=("CUE format check failed for $cue_file")
      fi
    done
  else
    echo "[WARN] No CUE files found in project"
  fi

  # 4. Basic validation for CUE syntax
  if find . -name "*.cue" -type f | head -1 | read; then
    echo "[INFO] Running CUE syntax validation..."
    for cue_file in $(find . -name "*.cue" -type f); do
      if ! cue vet "$cue_file" 2>/dev/null; then
        contract_errors+=("CUE syntax validation failed for $cue_file")
      fi
    done
  fi

  # Report results
  if [[ ''${#contract_errors[@]} -gt 0 ]]; then
    echo "[ERROR] Contract validation failed with errors:"
    for error in "''${contract_errors[@]}"; do
      echo "  - $error"
    done

    echo ""
    echo "To fix these issues:"
    echo "1. Add dir.cue with project policy definition"
    echo "2. Add contracts/flake.cue with technical boundary definition"
    echo "3. Ensure all CUE files are properly formatted (run 'cue fmt')"
    echo "4. Validate CUE syntax for all contract files"

    exit 1
  fi

  echo "[INFO] ✓ All CUE contract validations passed!"
  echo "CUE contract validation completed successfully" > $out
''