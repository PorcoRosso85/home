{
  description = "Flake contract system - TypeScript-based contract definitions for Nix flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            bun
            nodePackages.typescript
            nodePackages.typescript-language-server
          ];

          shellHook = ''
            echo "Flake Contract System Development Environment"
            echo "============================================"
            echo "Bun: $(bun --version)"
            echo ""
            echo "Available commands:"
            echo "  bun run type-check - Type check all TypeScript files"
            echo "  bun test           - Run tests"
            echo "  bun run format     - Format code"
            echo "  bun run start      - Run the application"
            echo ""
          '';
        };

        # Flake contract metadata (consumed by glue system)
        contract = {
          version = "0.1.0";
          interface = {
            inputs = {
              nixpkgs = "flake:nixpkgs";
              flake-utils = "flake:flake-utils";
            };
            outputs = {
              devShell = "derivation";
              contract = "attrset";
            };
          };
          capabilities = [ "bun" "typescript" "glue" ];
        };

        # Example Producer implementation (mock)
        packages.producer = pkgs.writeShellScriptBin "my-go-processor" ''
          # Mock implementation that outputs contract-compliant data
          echo '{
            "processed": 3,
            "failed": 0,
            "output": ["processed_item1", "processed_item2", "processed_item3"]
          }'
        '';

        # Example Consumer implementation (mock)
        packages.consumer = pkgs.writeShellScriptBin "bun-consumer" ''
          input=$(cat)
          echo "{
            \"summary\": \"Processed $(echo "$input" | ${pkgs.jq}/bin/jq -r '.output | length') items\",
            \"details\": $input
          }"
        '';

        # Contract validation checks using bun
        checks = {
          # Test contract validation logic
          contract-validator = pkgs.runCommand "contract-validator-test" {
            buildInputs = [ pkgs.bun ];
          } ''
            cp -r ${self} src
            cd src
            
            echo "🧪 Testing contract validator..."
            ${pkgs.bun}/bin/bun run ${./src/validator.ts}
            
            touch $out
          '';

          # Test producer output conforms to contract
          producer-contract-test = pkgs.runCommand "producer-contract-test" {
            buildInputs = [ pkgs.bun ];
          } ''
            # Get producer output
            PRODUCER_OUTPUT=$(${self.packages.${system}.producer}/bin/my-go-processor)
            
            # Create test script
            cat > test.ts << 'EOF'
            const output = JSON.parse(process.argv[2]);
            
            // Validate contract compliance
            if (!output.processed || typeof output.processed !== 'number') {
              console.error("❌ Missing or invalid 'processed' field");
              process.exit(1);
            }
            if (!output.failed || typeof output.failed !== 'number') {
              console.error("❌ Missing or invalid 'failed' field");
              process.exit(1);
            }
            if (!Array.isArray(output.output)) {
              console.error("❌ Missing or invalid 'output' array");
              process.exit(1);
            }
            
            console.log("✅ Producer output conforms to contract");
            EOF
            
            ${pkgs.bun}/bin/bun run test.ts "$PRODUCER_OUTPUT"
            touch $out
          '';

          # Integration test: Producer → Consumer pipeline
          integration-test = pkgs.runCommand "integration-test" {
            buildInputs = [ pkgs.bun pkgs.jq ];
          } ''
            # Run pipeline
            ${self.packages.${system}.producer}/bin/my-go-processor | \
            ${self.packages.${system}.consumer}/bin/bun-consumer > result.json
            
            # Validate final output
            if ${pkgs.jq}/bin/jq -e '.summary and .details' result.json > /dev/null; then
              echo "✅ Integration test passed"
            else
              echo "❌ Integration test failed"
              exit 1
            fi
            
            touch $out
          '';

          # Full test suite with bun
          test-suite = pkgs.runCommand "test-suite" {
            buildInputs = [ pkgs.bun ];
          } ''
            # Copy test files
            mkdir -p test
            cp ${./test/internal-test.ts} test/internal-test.ts 2>/dev/null || true
            cp ${./test-contract-validation.ts} test-contract-validation.ts
            
            # Run bun tests
            echo "🧪 Running full test suite..."
            ${pkgs.bun}/bin/bun test test-contract-validation.ts
            
            touch $out
          '';
        };

        # Package definition for the contract system
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "flake-contract";
          version = "0.1.0";
          src = ./.;
          
          buildInputs = [ pkgs.bun ];
          
          buildPhase = ''
            bun install --production
          '';
          
          installPhase = ''
            mkdir -p $out/bin $out/lib
            cp -r src $out/lib/
            cp package.json $out/lib/
            cat > $out/bin/flake-contract <<EOF
            #!/usr/bin/env bash
            exec ${pkgs.bun}/bin/bun run $out/lib/src/validator.ts "\$@"
            EOF
            chmod +x $out/bin/flake-contract
          '';
        };
      });
}