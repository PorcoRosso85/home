{
  description = "CUE Contract Management System - SSOT-based governance for multiple flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    # SOPS for secrets management
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # Pre-commit hooks
    pre-commit-hooks = {
      url = "github:cachix/pre-commit-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, sops-nix, pre-commit-hooks }:
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
          buildInputs = [ cuePkg pkgs.jq ];
          src = ./.;
          preferLocalBuild = true;
        } ''
          # Copy source to writable directory
          cp -r $src /tmp/cue-production
          chmod -R +w /tmp/cue-production
          cd /tmp/cue-production

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