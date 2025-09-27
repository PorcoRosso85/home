{
  description = "Nickel-based contract system for Nix flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Define packages first so they can be referenced by apps
        myPackages = rec {
          # Example producer using Nickel contract
          producer = pkgs.writeShellScriptBin "nickel-producer" ''
            ${pkgs.nickel}/bin/nickel export --format json << 'EOF'
            let contracts = import "${./contracts.ncl}" in
            {
              processed = 3,
              failed = 0,
              output = ["item1", "item2", "item3"],
            } & contracts.ProducerContract
            EOF
          '';

          # Example consumer
          consumer = pkgs.writeShellScriptBin "nickel-consumer" ''
            input_json=$(cat)
            
            # Create a temporary Nickel file with extracted values
            temp_file=$(mktemp --suffix=.ncl)
            trap 'rm -f "$temp_file"' EXIT
            
            # Extract values using optimized single jq call with error handling
            eval "$(echo "$input_json" | ${pkgs.jq}/bin/jq -r '@sh "processed=\(.processed) failed=\(.failed) output=\(.output | @json)"' || { echo "Error: Invalid JSON input" >&2; exit 1; })"
            
            cat > "$temp_file" << EOF
            let contracts = import "${./contracts.ncl}" in
            let input_data = {
              processed = $processed,
              failed = $failed,
              output = $output,
            } in
            {
              summary = "Processed " ++ std.to_string input_data.processed ++ " items with " ++ std.to_string input_data.failed ++ " failures",
              details = {
                processed = input_data.processed,
                failed = input_data.failed,
                output = input_data.output
              }
            } & contracts.ConsumerContract
            EOF
            ${pkgs.nickel}/bin/nickel export --format json "$temp_file"
          '';

          # Graph analyzer for contract graph visualization
          graph-analyzer = pkgs.writeShellScriptBin "nickel-graph-analyzer" ''
            echo "Contract Graph Analyzer"
            echo "======================="
            echo "Generating contract dependency graphs..."
            mkdir -p output
            ${pkgs.nickel}/bin/nickel export --format json ${./graph.ncl} > output/contract_graphs.json
            echo "✅ Contract graphs exported to output/contract_graphs.json"
            
            # Generate basic statistics
            echo ""
            echo "Graph Statistics:"
            echo "=================="
            ${pkgs.jq}/bin/jq -r '
              "Basic Graph: " + (.basic.nodes | length | tostring) + " nodes, " + (.basic.edges | length | tostring) + " edges\n" +
              "Large Scale Graph: " + (.large_scale.nodes | length | tostring) + " nodes, " + (.large_scale.edges | length | tostring) + " edges\n"
            ' output/contract_graphs.json
          '';

          # Error diagnostics tool
          error-diagnostics = pkgs.writeShellScriptBin "nickel-error-diagnostics" ''
            echo "Contract Error Diagnostics"
            echo "=========================="
            echo "Testing contract validation with error scenarios..."
            
            # Test valid data first
            echo "Testing valid producer data..."
            temp_file=$(mktemp --suffix=.ncl)
            cat > "$temp_file" << 'EOF'
            let error_diagnostics = import "${./error_diagnostics.ncl}" in
            error_diagnostics.valid_producer_data & error_diagnostics.ProducerContractWithDiagnostics
            EOF
            
            if ${pkgs.nickel}/bin/nickel export --format json "$temp_file" >/dev/null 2>&1; then
              echo "✅ Valid data test passed"
            else
              echo "❌ Valid data test failed"
            fi
            
            # Test error scenarios (document them without executing)
            echo ""
            echo "Available Error Scenarios:"
            echo "=========================="
            cat > "$temp_file" << 'EOF'
            let error_diagnostics = import "${./error_diagnostics.ncl}" in
            {
              error_labels = error_diagnostics.ErrorLabels,
              invalid_examples = std.record.fields error_diagnostics.invalid_data_examples,
            }
            EOF
            
            ${pkgs.nickel}/bin/nickel export --format json "$temp_file" | ${pkgs.jq}/bin/jq -r '
              "Error Labels: " + (.error_labels | keys | join(", ")) + "\n" +
              "Invalid Examples: " + (.invalid_examples | join(", "))
            '
            
            rm -f "$temp_file"
            echo ""
            echo "Use these labels for detailed contract violation reporting."
          '';

          # Default package points to producer  
          default = producer;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nickel
            jq
          ];

          shellHook = ''
            echo "Nickel Contract System"
            echo "====================="
            echo "Nickel: $(nickel --version)"
            echo ""
            echo "Commands:"
            echo "  nickel eval contracts.ncl      - Evaluate contracts"
            echo "  nickel query contracts.ncl      - Query contract schema"
            echo "  nickel typecheck contracts.ncl  - Type check contracts"
            echo ""
          '';
        };

        # Contract validation checks
        checks = {
          # Static type checking
          contract-typecheck = pkgs.runCommand "nickel-typecheck" {
            buildInputs = [ pkgs.nickel ];
          } ''
            cp ${./contracts.ncl} contracts.ncl
            ${pkgs.nickel}/bin/nickel typecheck contracts.ncl
            touch $out
          '';

          # Contract evaluation test
          contract-eval = pkgs.runCommand "nickel-eval" {
            buildInputs = [ pkgs.nickel ];
          } ''
            cp ${./contracts.ncl} contracts.ncl
            # Test that we can use the contracts by evaluating example data
            cat > test_eval.ncl << 'EOF'
            let contracts = import "contracts.ncl" in
            contracts.example_producer
            EOF
            ${pkgs.nickel}/bin/nickel eval test_eval.ncl > /dev/null
            echo "✅ Contracts evaluated successfully"
            touch $out
          '';

          # Validate example data
          validate-example = pkgs.runCommand "validate-example" {
            buildInputs = [ pkgs.nickel pkgs.jq ];
          } ''
            cat > validate.ncl << 'EOF'
            let contracts = import "contracts.ncl" in
            let test_data = {
              processed = 5,
              failed = 0,
              output = ["a", "b", "c"],
            } in
            contracts.validate_producer test_data
            EOF
            
            cp ${./contracts.ncl} contracts.ncl
            ${pkgs.nickel}/bin/nickel eval validate.ncl
            touch $out
          '';

          # Pipeline test using the test script
          pipeline-test = pkgs.runCommand "pipeline-test" {
            buildInputs = with pkgs; [ nickel jq bash ];
          } ''
            # Copy source files
            cp -r ${./.} source
            chmod -R +w source
            cd source
            
            # Copy test script explicitly
            cp ${./test/pipeline_test.sh} ./pipeline_test.sh
            chmod +x ./pipeline_test.sh
            
            # Run the test
            bash ./pipeline_test.sh
            touch $out
          '';

          # Advanced test - graph analysis
          graph-analysis-test = pkgs.runCommand "graph-analysis-test" {
            buildInputs = with pkgs; [ nickel jq ];
          } ''
            cp ${./graph.ncl} graph.ncl
            
            # Test graph structure export
            ${pkgs.nickel}/bin/nickel export --format json graph.ncl > graph_output.json
            
            # Verify basic graph structure
            BASIC_NODES=$(${pkgs.jq}/bin/jq '.basic.nodes | length' graph_output.json)
            BASIC_EDGES=$(${pkgs.jq}/bin/jq '.basic.edges | length' graph_output.json)
            LARGE_NODES=$(${pkgs.jq}/bin/jq '.large_scale.nodes | length' graph_output.json)
            LARGE_EDGES=$(${pkgs.jq}/bin/jq '.large_scale.edges | length' graph_output.json)
            
            echo "Graph Analysis Results:"
            echo "Basic graph: $BASIC_NODES nodes, $BASIC_EDGES edges"
            echo "Large scale graph: $LARGE_NODES nodes, $LARGE_EDGES edges"
            
            # Validate minimum complexity for large scale
            if [ "$LARGE_NODES" -ge 10 ]; then
              echo "✅ Large scale graph has sufficient complexity"
            else
              echo "❌ Large scale graph too simple"
              exit 1
            fi
            
            touch $out
          '';

          # Advanced test - error diagnostics
          error-diagnostics-test = pkgs.runCommand "error-diagnostics-test" {
            buildInputs = with pkgs; [ nickel jq ];
          } ''
            cp ${./error_diagnostics.ncl} error_diagnostics.ncl
            
            # Test error diagnostics structure
            cat > test_diagnostics.ncl << 'EOF'
            let error_diagnostics = import "error_diagnostics.ncl" in
            {
              error_labels = error_diagnostics.ErrorLabels,
              valid_data = error_diagnostics.valid_producer_data,
              invalid_examples_count = std.array.length (std.record.values error_diagnostics.invalid_data_examples),
            }
            EOF
            
            ${pkgs.nickel}/bin/nickel export --format json test_diagnostics.ncl > diagnostics_output.json
            
            # Verify error diagnostics structure
            ERROR_LABELS=$(${pkgs.jq}/bin/jq '.error_labels | length' diagnostics_output.json)
            INVALID_EXAMPLES=$(${pkgs.jq}/bin/jq '.invalid_examples_count' diagnostics_output.json)
            
            echo "Error Diagnostics Results:"
            echo "Error labels defined: $ERROR_LABELS"
            echo "Invalid examples: $INVALID_EXAMPLES"
            
            if [ "$ERROR_LABELS" -ge 4 ] && [ "$INVALID_EXAMPLES" -ge 4 ]; then
              echo "✅ Error diagnostics comprehensive"
            else
              echo "❌ Error diagnostics insufficient"
              exit 1
            fi
            
            touch $out
          '';

          # Contract compatibility check (FR-002)
          contract-compatibility = pkgs.runCommand "contract-compatibility" {
            buildInputs = with pkgs; [ nickel jq ];
          } ''
            cp ${./contracts.ncl} contracts.ncl
            cp ${./compatibility_check.ncl} compatibility_check.ncl
            
            # Test contract compatibility validation
            echo "Testing contract compatibility validation..."
            ${pkgs.nickel}/bin/nickel export --format json compatibility_check.ncl > compatibility_output.json
            
            # Verify compatibility result structure
            OVERALL_COMPATIBLE=$(${pkgs.jq}/bin/jq '.compatibility_result.overall_compatible' compatibility_output.json)
            OUTPUT_MAPPING=$(${pkgs.jq}/bin/jq '.compatibility_result.output_mapping_valid' compatibility_output.json)
            NUMERIC_TYPES=$(${pkgs.jq}/bin/jq '.compatibility_result.numeric_types_valid' compatibility_output.json)
            
            echo "Compatibility Results:"
            echo "Overall compatible: $OVERALL_COMPATIBLE"
            echo "Output mapping valid: $OUTPUT_MAPPING" 
            echo "Numeric types valid: $NUMERIC_TYPES"
            
            if [ "$OVERALL_COMPATIBLE" = "true" ]; then
              echo "✅ Contract compatibility validation passed"
            else
              echo "❌ Contract compatibility validation failed"
              exit 1
            fi
            
            touch $out
          '';

          # Advanced integration test
          advanced-test = pkgs.runCommand "advanced-test" {
            buildInputs = with pkgs; [ nickel jq bash ];
          } ''
            cp ${./graph.ncl} graph.ncl
            cp ${./error_diagnostics.ncl} error_diagnostics.ncl
            
            # Test graph functionality
            echo "Testing advanced graph functionality..."
            ${pkgs.nickel}/bin/nickel export --format json graph.ncl > graph_test.json
            NODES=$(${pkgs.jq}/bin/jq '.large_scale.nodes | length' graph_test.json)
            
            if [ "$NODES" -ge 10 ]; then
              echo "✅ Advanced graph test passed ($NODES nodes)"
            else
              echo "❌ Advanced graph test failed"
              exit 1
            fi
            
            # Test error diagnostics structure  
            echo "Testing error diagnostics structure..."
            cat > test_diagnostics.ncl << 'EOF'
            let error_diagnostics = import "error_diagnostics.ncl" in
            {
              error_labels = error_diagnostics.ErrorLabels,
              valid_data = error_diagnostics.valid_producer_data,
            }
            EOF
            
            ${pkgs.nickel}/bin/nickel export --format json test_diagnostics.ncl > /dev/null
            echo "✅ Error diagnostics structure test passed"
            
            echo "✅ All advanced integration tests passed"
            touch $out
          '';

          # Pure producer contract validation
          producer-contract-pure = pkgs.runCommand "producer-contract-pure" {
            buildInputs = [ pkgs.nickel pkgs.jq ];
          } ''
            # Producer実行 → Nickel契約検証 → 成功時に$out作成
            ${myPackages.producer}/bin/nickel-producer > producer_output.json
            
            # 純粋な契約検証のみ（内部ロジック不問）
            ${pkgs.jq}/bin/jq -r '.processed, .failed, (.output | tostring)' producer_output.json > /dev/null
            
            # Extract JSON values and create Nickel validation script
            PROCESSED=$(${pkgs.jq}/bin/jq -r '.processed' producer_output.json)
            FAILED=$(${pkgs.jq}/bin/jq -r '.failed' producer_output.json)
            OUTPUT=$(${pkgs.jq}/bin/jq -c '.output' producer_output.json)
            
            cat > validate_producer.ncl << EOF
            let contracts = import "${./contracts.ncl}" in
            let test_data = {
              processed = $PROCESSED,
              failed = $FAILED,
              output = $OUTPUT,
            } in
            test_data & contracts.ProducerContract
            EOF
            
            ${pkgs.nickel}/bin/nickel eval validate_producer.ncl
            
            touch $out
          '';

          # Pure consumer contract validation
          consumer-contract-pure = pkgs.runCommand "consumer-contract-pure" {
            buildInputs = [ pkgs.nickel pkgs.jq ];
          } ''
            # 3つの入力パターンでConsumer契約検証
            test_cases='[
              {"processed":0,"failed":0,"output":[]},
              {"processed":5,"failed":1,"output":["a","b","c"]},
              {"processed":1000,"failed":50,"output":["batch1","batch2"]}
            ]'
            
            test_counter=0
            echo "$test_cases" | ${pkgs.jq}/bin/jq -c '.[]' | while read case; do
              test_counter=$((test_counter + 1))
              echo "Testing case $test_counter: $case"
              
              # Feed test case to consumer and capture output
              consumer_output=$(echo "$case" | ${myPackages.consumer}/bin/nickel-consumer)
              
              # Extract consumer output fields
              SUMMARY=$(echo "$consumer_output" | ${pkgs.jq}/bin/jq -r '.summary|@json')
              PROCESSED=$(echo "$consumer_output" | ${pkgs.jq}/bin/jq -r '.details.processed')
              FAILED=$(echo "$consumer_output" | ${pkgs.jq}/bin/jq -r '.details.failed')
              OUTPUT=$(echo "$consumer_output" | ${pkgs.jq}/bin/jq -c '.details.output')
              
              # Create validation script for this test case
              cat > validate_consumer_$test_counter.ncl << EOF
              let contracts = import "${./contracts.ncl}" in
              let test_data = {
                summary = $SUMMARY,
                details = {
                  processed = $PROCESSED,
                  failed = $FAILED,
                  output = $OUTPUT,
                }
              } in
              test_data & contracts.ConsumerContract
            EOF
              
              ${pkgs.nickel}/bin/nickel eval validate_consumer_$test_counter.ncl
              echo "✅ Case $test_counter validated successfully"
            done
            
            touch $out
          '';
        };

        # Reference the packages defined in let
        packages = myPackages;

        # Apps for direct execution
        apps = rec {
          producer = flake-utils.lib.mkApp {
            drv = myPackages.producer;
          };
          consumer = flake-utils.lib.mkApp {
            drv = myPackages.consumer;
          };
          graph-analyzer = flake-utils.lib.mkApp {
            drv = myPackages.graph-analyzer;
          };
          error-diagnostics = flake-utils.lib.mkApp {
            drv = myPackages.error-diagnostics;
          };
          default = producer;
        };

        # Contract metadata
        contract = {
          version = "0.1.0";
          type = "nickel";
          schema = ./contracts.ncl;
          capabilities = [ "static-typing" "contract-validation" ];
        };
      });
}