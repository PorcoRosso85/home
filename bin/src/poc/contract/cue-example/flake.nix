{
  description = "CUE Contract Management System - SSOT-based governance for multiple flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";


    # Pre-commit hooks
    pre-commit-hooks = {
      url = "github:cachix/pre-commit-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, pre-commit-hooks }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        cuePkg = pkgs.cue;

        # Contract file discovery (pure eval, stable sorting)
        listContracts = pkgs.writeText "list-contracts.nix" ''
          let
            lib = import <nixpkgs/lib>;

            # Recursively find all contract.cue files under contracts/
            findContracts = baseDir: dir:
              let
                fullPath = baseDir + "/" + dir;
                contents = builtins.readDir fullPath;
                files = lib.mapAttrsToList (name: type:
                  let
                    relativePath = if dir == "" then name else dir + "/" + name;
                    absolutePath = fullPath + "/" + name;
                  in
                  if type == "directory" then
                    findContracts baseDir relativePath
                  else if name == "contract.cue" then
                    [ absolutePath ]
                  else
                    []
                ) contents;
              in
                lib.flatten files;

            # Sort for stable ordering (UTF-8 sort)
            contracts = lib.sort (a: b: a < b) (findContracts ./. "contracts");
          in
            contracts
        '';

        # Generate directory-specific index files
        productionIndexJson = pkgs.runCommand "production-index.json" {
          buildInputs = [ pkgs.findutils pkgs.jq ];
          src = ./.;
          preferLocalBuild = true;
        } ''
          # Copy source to writable directory
          cp -r $src /tmp/contract-discovery
          cd /tmp/contract-discovery

          # Find production contract.cue files and create JSON array
          if [ -d "contracts/production" ]; then
            find contracts/production -name "contract.cue" -type f | sort | jq -R . | jq -s . > $out
          else
            echo "[]" > $out
          fi
        '';

        examplesIndexJson = pkgs.runCommand "examples-index.json" {
          buildInputs = [ pkgs.findutils pkgs.jq ];
          src = ./.;
          preferLocalBuild = true;
        } ''
          # Copy source to writable directory
          cp -r $src /tmp/contract-discovery
          cd /tmp/contract-discovery

          # Find example contract.cue files and create JSON array
          if [ -d "contracts/examples" ]; then
            find contracts/examples -name "contract.cue" -type f | sort | jq -R . | jq -s . > $out
          else
            echo "[]" > $out
          fi
        '';

        testIndexJson = pkgs.runCommand "test-index.json" {
          buildInputs = [ pkgs.findutils pkgs.jq ];
          src = ./.;
          preferLocalBuild = true;
        } ''
          # Copy source to writable directory
          cp -r $src /tmp/contract-discovery
          cd /tmp/contract-discovery

          # Find test contract.cue files and create JSON array
          if [ -d "contracts/test" ]; then
            find contracts/test -name "contract.cue" -type f | sort | jq -R . | jq -s . > $out
          else
            echo "[]" > $out
          fi
        '';

        # Production contract validation (strict)
        productionValidation = pkgs.runCommand "production-validation" {
          buildInputs = [ cuePkg pkgs.jq pkgs.findutils ];
          src = ./.;
          preferLocalBuild = true;
        } ''
          # Copy source to writable directory
          cp -r $src /tmp/cue-production
          chmod -R +w /tmp/cue-production
          cd /tmp/cue-production

          # PHASE 2.3: Strict existence checking - every production directory must have contract.cue
          echo "SSOT Enforcement: Checking contract.cue existence for all production directories..."

          missing_contracts=""
          if [ -d "contracts/production" ]; then
            # Find all subdirectories under contracts/production/
            while IFS= read -r dir; do
              # Extract directory name (remove contracts/production/ prefix)
              dir_name=$(basename "$dir")
              contract_file="$dir/contract.cue"

              if [ ! -f "$contract_file" ]; then
                echo "ERROR: Missing contract.cue in directory: $dir" >&2
                missing_contracts="$missing_contracts $dir_name"
              else
                echo "✓ Found contract.cue in: $dir"
              fi
            done < <(find contracts/production -type d -mindepth 1 -maxdepth 1 | sort)
          fi

          # Fail fast if any contracts are missing
          if [ -n "$missing_contracts" ]; then
            echo "" >&2
            echo "🚫 SSOT VIOLATION: Missing contract.cue files!" >&2
            echo "The following production directories lack required contracts:" >&2
            for missing in $missing_contracts; do
              echo "  - contracts/production/$missing/contract.cue" >&2
            done
            echo "" >&2
            echo "SSOT principle: Every managed directory must have a contract" >&2
            echo "Create the missing contract.cue files or remove unused directories" >&2
            exit 1
          fi

          echo "✅ Contract existence verified: All production directories have contract.cue"

          # Ensure tools directory exists and copy index.json for CUE consumption
          mkdir -p tools
          cp ${productionIndexJson} tools/index.json

          # Extract contract data from discovered files and inject into validation
          echo "Reading production contract files from index.json..."
          cat tools/index.json

          # Create contracts data file
          echo "package tools" > tools/contracts-data.cue
          echo "" >> tools/contracts-data.cue
          echo "// Production contract data injected from discovered files" >> tools/contracts-data.cue
          echo "validation: {" >> tools/contracts-data.cue
          echo "  contracts: [" >> tools/contracts-data.cue

          # Process each contract file listed in index.json
          contract_count=0
          while IFS= read -r contract_file; do
            if [ -f "$contract_file" ]; then
              echo "Processing production contract: $contract_file"
              # Export contract data and append to contracts array
              if contract_data=$(cue export "$contract_file" 2>/dev/null); then
                # Extract the actual contract object (assuming one exported definition)
                contract_name=$(echo "$contract_data" | jq -r 'keys[0]')
                if [ "$contract_name" != "null" ] && [ -n "$contract_name" ]; then
                  echo "$contract_data" | jq -r ".$contract_name" >> /tmp/contract_$contract_count.json
                  if [ $contract_count -gt 0 ]; then
                    echo "," >> tools/contracts-data.cue
                  fi
                  cat /tmp/contract_$contract_count.json >> tools/contracts-data.cue
                  contract_count=$((contract_count + 1))
                fi
              else
                echo "Error: Could not export production contract $contract_file" >&2
                exit 1
              fi
            fi
          done < <(jq -r '.[]' tools/index.json)

          echo "" >> tools/contracts-data.cue
          echo "  ]" >> tools/contracts-data.cue
          echo "}" >> tools/contracts-data.cue

          echo "Processed $contract_count production contracts"

          # Run strict aggregate validation with injected data
          echo "Running strict production validation..."
          if cue export ./tools/aggregate.cue ./tools/contracts-data.cue; then
            echo "production: all checks passed"
            touch $out
          else
            echo "production: validation failed" >&2
            exit 1
          fi
        '';

        # Example contract validation (educational)
        examplesValidation = pkgs.runCommand "examples-validation" {
          buildInputs = [ cuePkg pkgs.jq ];
          src = ./.;
          preferLocalBuild = true;
        } ''
          # Copy source to writable directory
          cp -r $src /tmp/cue-examples
          chmod -R +w /tmp/cue-examples
          cd /tmp/cue-examples

          # Ensure tools directory exists
          mkdir -p tools
          cp ${examplesIndexJson} tools/index.json

          echo "Validating example contracts (educational mode)..."
          cat tools/index.json

          # For examples, just check syntax and basic structure
          example_count=0
          while IFS= read -r contract_file; do
            if [ -f "$contract_file" ]; then
              echo "Checking example syntax: $contract_file"
              if cue vet "$contract_file" 2>/dev/null; then
                echo "  ✓ Syntax valid"
              else
                echo "  ⚠ Syntax issues (educational example)"
              fi
              example_count=$((example_count + 1))
            fi
          done < <(jq -r '.[]' tools/index.json)

          echo "examples: checked $example_count example contracts"
          touch $out
        '';

        # Test contract validation (syntax only)
        testValidation = pkgs.runCommand "test-validation" {
          buildInputs = [ cuePkg pkgs.jq ];
          src = ./.;
          preferLocalBuild = true;
        } ''
          # Copy source to writable directory
          cp -r $src /tmp/cue-test
          chmod -R +w /tmp/cue-test
          cd /tmp/cue-test

          # Ensure tools directory exists
          mkdir -p tools
          cp ${testIndexJson} tools/index.json

          echo "Validating test contracts (syntax only)..."
          cat tools/index.json

          # For test contracts, only check basic syntax
          test_count=0
          while IFS= read -r contract_file; do
            if [ -f "$contract_file" ]; then
              echo "Checking test syntax: $contract_file"
              if cue fmt --check "$contract_file" 2>/dev/null; then
                echo "  ✓ Syntax valid"
              else
                echo "  ⚠ Syntax formatting (test fixture)"
              fi
              test_count=$((test_count + 1))
            fi
          done < <(jq -r '.[]' tools/index.json)

          echo "test: checked $test_count test contracts"
          touch $out
        '';

        # Plaintext secrets detection (using unified script)
        secretsCheck = ''
          # Run the unified script with bash explicitly
          bash tools/check-secrets.sh
        '';


      in
      {
        # Development shell with all required tools
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            cuePkg
            sops
            pre-commit
            nixpkgs-fmt
            shellcheck
            shfmt
          ];

          shellHook = ''
            echo "=' CUE Contract Management System"
            echo "Available commands:"
            echo "  cue fmt ./...      - Format CUE files"
            echo "  cue vet ./...      - Validate CUE files"
            echo "  cue export ./...   - Export CUE to JSON"
            echo "  nix flake check    - Run all checks"
            echo "  pre-commit run --all-files - Run pre-commit hooks"
          '';
        };

        # Standardized checks with fixed naming
        checks = {
          # CUE formatting check
          cueFmt = pkgs.runCommand "cue-fmt-check" {
            buildInputs = [ cuePkg ];
            src = ./.;
          } ''
            # Copy source to writable directory
            cp -r $src /tmp/cue-check
            chmod -R +w /tmp/cue-check
            cd /tmp/cue-check

            # Check if files are properly formatted (dry-run)
            if cue fmt --check ./...; then
              echo "cueFmt: all files properly formatted"
              touch $out
            else
              echo "cueFmt: formatting issues detected" >&2
              exit 1
            fi
          '';

          # CUE validation check
          cueVet = pkgs.runCommand "cue-vet-check" {
            buildInputs = [ cuePkg ];
            src = ./.;
          } ''
            # Copy source to temporary directory
            cp -r $src /tmp/cue-vet
            cd /tmp/cue-vet

            if cue vet -c=false ./...; then
              echo "cueVet: validation passed"
              touch $out
            else
              echo "cueVet: validation failed" >&2
              exit 1
            fi
          '';

          # CUE export check
          cueExport = pkgs.runCommand "cue-export-check" {
            buildInputs = [ cuePkg ];
            src = ./.;
          } ''
            # Copy source to temporary directory
            cp -r $src /tmp/cue-export
            cd /tmp/cue-export

            if cue export ./...; then
              echo "cueExport: export successful"
              touch $out
            else
              echo "cueExport: export failed" >&2
              exit 1
            fi
          '';

          # Production contracts validation (strict)
          contractsProduction = productionValidation;

          # Example contracts validation (educational)
          contractsExamples = examplesValidation;

          # Test contracts validation (syntax only)
          contractsTest = testValidation;

          # Plaintext secrets detection
          secretsPlaintext = pkgs.runCommand "secrets-plaintext-check" {
            buildInputs = [ pkgs.bash pkgs.gnugrep pkgs.findutils ];
            src = ./.;
          } ''
            # Copy source to temporary directory
            cp -r $src /tmp/secrets-check
            cd /tmp/secrets-check
            ${secretsCheck}
            touch $out
          '';

          # SystemD service verification (if applicable)
          systemdVerify = pkgs.runCommand "systemd-verify-check" {
            buildInputs = [ pkgs.systemd ];
            src = ./.;
          } ''
            # Copy source to temporary directory
            cp -r $src /tmp/systemd-check
            cd /tmp/systemd-check

            # Find systemd service files
            if find . -name "*.service" -type f | head -1 > /dev/null; then
              echo "systemdVerify: checking service files"
              find . -name "*.service" -exec systemd-analyze verify {} \;
            else
              echo "systemdVerify: no service files found, skipping"
            fi

            touch $out
          '';

          # Generated artifacts prevention (SSOT governance)
          noGeneratedArtifacts = pkgs.runCommand "no-generated-artifacts-check" {
            buildInputs = [ pkgs.findutils pkgs.gnugrep ];
            src = ./.;
          } ''
            cd $src

            echo "noGeneratedArtifacts: checking for prohibited generated files"

            # Define patterns for generated artifacts that should never be tracked
            prohibited_files=""

            # Check for tools/index.json (main generated index)
            if [ -f "tools/index.json" ]; then
              echo "ERROR: Found prohibited file: tools/index.json" >&2
              prohibited_files="$prohibited_files tools/index.json"
            fi

            # Check for any *-index.json files in tools/ directory
            if find tools -name "*-index.json" -type f 2>/dev/null | grep -q .; then
              echo "ERROR: Found prohibited generated index files:" >&2
              find tools -name "*-index.json" -type f 2>/dev/null | sed 's/^/  /' >&2
              prohibited_files="$prohibited_files $(find tools -name "*-index.json" -type f 2>/dev/null | tr '\n' ' ')"
            fi

            # Check for contracts-data.cue (injected data file)
            if [ -f "tools/contracts-data.cue" ]; then
              echo "ERROR: Found prohibited file: tools/contracts-data.cue" >&2
              prohibited_files="$prohibited_files tools/contracts-data.cue"
            fi

            # Check for other common generated artifacts patterns
            if find . -name "*.generated.*" -type f 2>/dev/null | grep -q .; then
              echo "ERROR: Found files with .generated. pattern:" >&2
              find . -name "*.generated.*" -type f 2>/dev/null | sed 's/^/  /' >&2
              prohibited_files="$prohibited_files $(find . -name "*.generated.*" -type f 2>/dev/null | tr '\n' ' ')"
            fi

            # Check for .build/ or build/ directories with artifacts
            for build_dir in .build build; do
              if [ -d "$build_dir" ] && find "$build_dir" -type f 2>/dev/null | grep -q .; then
                echo "ERROR: Found build directory with artifacts: $build_dir/" >&2
                prohibited_files="$prohibited_files $build_dir/"
              fi
            done

            # Final verdict
            if [ -n "$prohibited_files" ]; then
              echo "" >&2
              echo "SSOT VIOLATION: Generated artifacts found in source tree!" >&2
              echo "These files should be generated at build time, not tracked in Git:" >&2
              echo "$prohibited_files" | tr ' ' '\n' | sed 's/^/  - /' >&2
              echo "" >&2
              echo "To fix: Remove these files and ensure .gitignore prevents tracking" >&2
              exit 1
            else
              echo "noGeneratedArtifacts: ✓ No prohibited artifacts found"
              echo "SSOT principle enforced: source tree contains only source files"
              touch $out
            fi
          '';

          # Breaking changes detection (SSOT governance) - forced rebuild
          breakingChanges = pkgs.runCommand "breaking-changes-check" {
            buildInputs = [ cuePkg pkgs.jq ];
            src = ./.;
          } ''
            # Copy source to writable directory
            cp -r $src /tmp/breaking-changes
            chmod -R +w /tmp/breaking-changes
            cd /tmp/breaking-changes

            echo "breakingChanges: checking for breaking changes against baseline"

            # Ensure baseline exists
            if [ ! -f "baseline/production.json" ]; then
              echo "ERROR: Missing baseline/production.json for breaking change detection" >&2
              echo "To create baseline: nix develop --command bash -c 'cue export contracts/production/api/contract.cue > baseline/api.json && cue export contracts/production/database/contract.cue > baseline/database.json && cue export contracts/production/cache/contract.cue > baseline/cache.json && jq -s \".[0] * .[1] * .[2]\" baseline/api.json baseline/cache.json baseline/database.json > baseline/production.json'" >&2
              exit 1
            fi

            # Export current production contracts
            echo "Exporting current production contracts..."
            mkdir -p tools

            # Export individual contracts
            if cue export contracts/production/api/contract.cue > tools/current-api.json 2>/dev/null && \
               cue export contracts/production/database/contract.cue > tools/current-database.json 2>/dev/null && \
               cue export contracts/production/cache/contract.cue > tools/current-cache.json 2>/dev/null; then
              echo "✓ Current contracts exported successfully"
            else
              echo "ERROR: Failed to export current production contracts" >&2
              exit 1
            fi

            # Combine current contracts
            jq -s '.[0] * .[1] * .[2]' tools/current-api.json tools/current-database.json tools/current-cache.json > tools/current-production.json

            # Simple JSON-based breaking change detection
            echo "Running breaking change analysis..."

            # Compare baseline vs current using jq
            breaking_changes=""

            # Check for service removal (service present in baseline but not current)
            missing_services=$(jq -r 'keys[]' baseline/production.json | while read service; do
              if ! jq -e ".\"$service\"" tools/current-production.json > /dev/null 2>&1; then
                echo "$service"
              fi
            done)

            if [ -n "$missing_services" ]; then
              breaking_changes="$breaking_changes\nRemoved services: $missing_services"
            fi

            # Check for capability reduction in each service
            capability_changes_file=$(mktemp)
            jq -r 'keys[]' baseline/production.json | while read service; do
              if jq -e ".\"$service\"" tools/current-production.json > /dev/null 2>&1; then
                # Compare provides arrays
                baseline_provides=$(jq -r ".\"$service\".provides[]?.id" baseline/production.json 2>/dev/null | sort | tr '\n' ' ')
                current_provides=$(jq -r ".\"$service\".provides[]?.id" tools/current-production.json 2>/dev/null | sort | tr '\n' ' ')

                if [ "$baseline_provides" != "$current_provides" ]; then
                  echo "Service $service: capability changes detected"
                  echo "  Baseline: $baseline_provides"
                  echo "  Current:  $current_provides"
                  echo "Service $service capability changes" >> "$capability_changes_file"
                fi
              fi
            done

            # Read capability changes from file
            if [ -s "$capability_changes_file" ]; then
              breaking_changes="$breaking_changes\n$(cat "$capability_changes_file")"
            fi
            rm -f "$capability_changes_file"

            # Check results
            if [ -n "$breaking_changes" ]; then
              echo "" >&2
              echo "🚫 BREAKING CHANGES DETECTED!" >&2
              echo "The following breaking changes were found:" >&2
              echo -e "$breaking_changes" | sed 's/^/  - /' >&2
              echo "" >&2
              echo "Breaking changes violate SSOT governance rules." >&2
              echo "Either revert the changes or update the baseline intentionally." >&2
              exit 1
            else
              echo "✅ No breaking changes detected"
              echo "breakingChanges: all production contracts are backward compatible"
              touch $out
            fi
          '';

          # CUE vendor dependency check (SSOT governance)
          vendorCheck = pkgs.runCommand "vendor-check" {
            buildInputs = [ cuePkg pkgs.jq ];
            src = ./.;
            preferLocalBuild = true;
          } ''
            # Copy source to writable directory
            cp -r $src /tmp/vendor-check
            chmod -R +w /tmp/vendor-check
            cd /tmp/vendor-check

            echo "vendorCheck: verifying CUE module dependency consistency"

            # Check if cue.mod/module.cue exists and is valid
            if [ ! -f "cue.mod/module.cue" ]; then
              echo "ERROR: Missing cue.mod/module.cue - CUE module not properly initialized" >&2
              echo "To fix: Run 'cue mod init <module-name>'" >&2
              exit 1
            fi

            # Validate module.cue syntax
            if ! cue export cue.mod/module.cue >/dev/null 2>&1; then
              echo "ERROR: Invalid syntax in cue.mod/module.cue" >&2
              echo "To fix: Check cue.mod/module.cue for syntax errors" >&2
              exit 1
            fi

            # Check if we have any external imports that need vendoring
            external_imports=$(find . -name "*.cue" -not -path "./cue.mod/*" -not -path "./vendor/*" | \
              xargs grep -l "^import" | \
              xargs grep "^import" | \
              grep -v "example.corp/contract-system" | \
              grep -E '"[^./]' || true)

            if [ -n "$external_imports" ]; then
              echo "External imports detected that may need vendoring:"
              echo "$external_imports" | sed 's/^/  /'

              # Check if vendor directory exists
              if [ ! -d "vendor" ]; then
                echo "WARNING: External imports found but no vendor/ directory" >&2
                echo "Consider running 'cue mod vendor' if external dependencies are needed" >&2
                echo "Or ensure all imports are local to this module" >&2
              fi
            fi

            # If vendor directory exists, validate it's consistent
            if [ -d "vendor" ]; then
              echo "Vendor directory found - checking consistency..."

              # Check if vendor directory has any content
              if [ -z "$(find vendor -name "*.cue" 2>/dev/null)" ]; then
                echo "WARNING: Empty vendor/ directory detected" >&2
                echo "Consider removing empty vendor/ or running 'cue mod vendor'" >&2
              else
                echo "Vendor directory contains CUE files - assuming properly vendored"

                # Verify vendor directory structure is valid
                if ! find vendor -name "*.cue" | head -1 | xargs cue vet >/dev/null 2>&1; then
                  echo "ERROR: Invalid CUE files in vendor/ directory" >&2
                  echo "To fix: Run 'cue mod vendor' to refresh dependencies" >&2
                  exit 1
                fi
              fi
            fi

            # Check for loose .cue files that might be dependencies
            loose_deps=$(find . -maxdepth 2 -name "*.cue" -not -path "./cue.mod/*" \
              -not -path "./vendor/*" -not -path "./schema/*" -not -path "./contracts/*" \
              -not -path "./tests/*" -not -path "./tools/*" -not -path "./secrets/*" \
              -not -path "./baseline/*" -not -path "./docs/*" | head -5)

            if [ -n "$loose_deps" ]; then
              echo "INFO: Found loose .cue files in root - verify they're intentional:"
              echo "$loose_deps" | sed 's/^/  /'
            fi

            # Verify current module name matches imports
            module_name=$(cue export cue.mod/module.cue | jq -r '.module // empty')
            if [ -n "$module_name" ]; then
              echo "Module name: $module_name"

              # Check if any imports reference the current module (circular dependency)
              circular_refs=$(find . -name "*.cue" -not -path "./cue.mod/*" -not -path "./vendor/*" | \
                xargs grep -l "import.*$module_name" || true)

              if [ -n "$circular_refs" ]; then
                echo "WARNING: Potential circular dependency - module imports itself:" >&2
                echo "$circular_refs" | sed 's/^/  /' >&2
              fi
            fi

            echo "vendorCheck: ✓ CUE module dependency structure validated"
            echo "SSOT principle enforced: dependency consistency maintained"
            touch $out
          '';
        };

        # Minimal smoke tests
        nixosTests = {
          smoke = pkgs.runCommand "smoke-test" {
            buildInputs = [ cuePkg ];
            src = ./.;
          } ''
            cd $src
            echo "smoke: basic functionality test"

            # Test 1: CUE tools availability
            cue version

            # Test 2: Basic validation
            if [ -f "schema/contract.cue" ]; then
              cue vet schema/contract.cue
            fi

            # Test 3: Contract discovery
            echo "smoke: testing contract discovery"
            find contracts -name "contract.cue" -type f || true

            echo "smoke: all tests passed"
            touch $out
          '';
        };

        # Pre-commit configuration
        pre-commit-check = pre-commit-hooks.lib.${system}.run {
          src = ./.;
          hooks = {
            # CUE formatting
            cue-fmt = {
              enable = true;
              name = "cue fmt";
              entry = "${cuePkg}/bin/cue fmt";
              files = "\\.cue$";
            };

            # CUE validation
            cue-vet = {
              enable = true;
              name = "cue vet";
              entry = "${cuePkg}/bin/cue vet";
              files = "\\.cue$";
              pass_filenames = false;
            };

            # Nix flake check
            flake-check = {
              enable = true;
              name = "nix flake check";
              entry = "nix flake check -L";
              pass_filenames = false;
              always_run = true;
            };

            # Shell formatting
            shfmt = {
              enable = true;
              name = "shfmt";
              entry = "${pkgs.shfmt}/bin/shfmt -w";
              files = "\\.(sh|bash)$";
            };

            # Shell linting
            shellcheck = {
              enable = true;
              name = "shellcheck";
              entry = "${pkgs.shellcheck}/bin/shellcheck";
              files = "\\.(sh|bash)$";
            };

            # Secrets detection
            secrets-check = {
              enable = true;
              name = "secrets plaintext detection";
              entry = "${secretsCheck}";
              pass_filenames = false;
              always_run = true;
            };

            # Nix formatting
            nixpkgs-fmt = {
              enable = true;
              name = "nixpkgs-fmt";
              entry = "${pkgs.nixpkgs-fmt}/bin/nixpkgs-fmt";
              files = "\\.nix$";
            };
          };
        };

        # Formatter for `nix fmt`
        formatter = pkgs.nixpkgs-fmt;

        # Apps for convenience
        apps = {
          # Quick validation
          validate = flake-utils.lib.mkApp {
            drv = pkgs.writeShellScript "validate" ''
              echo "= Running CUE Contract validation..."
              cue fmt ./...
              cue vet ./...
              cue export ./...
              echo " Validation complete"
            '';
          };

          # Full check suite
          check-all = flake-utils.lib.mkApp {
            drv = pkgs.writeShellScript "check-all" ''
              echo ">� Running full check suite..."
              nix flake check -L --pure-eval --no-write-lock-file
              echo " All checks passed"
            '';
          };
        };
      }
    );
}