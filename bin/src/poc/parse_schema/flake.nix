{
  description = "Contract testing system using ajv-cli for Unix tool validation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages = {
          # tool1の出力を検証
          test-producer = pkgs.writeShellScriptBin "test-producer" ''
            #!/usr/bin/env bash
            set -euo pipefail
            
            if [ $# -lt 2 ]; then
              echo "Usage: test-producer <schema.json> <tool-command>"
              echo "Example: test-producer log-schema.json './my-logger'"
              exit 1
            fi
            
            schema="$1"
            shift
            command="$@"
            
            echo "Testing producer output against schema: $schema"
            echo "Running: $command"
            
            # ツールを実行してajvで検証
            $command | ${pkgs.nodePackages.ajv-cli}/bin/ajv validate -s "$schema" -d -
            
            if [ $? -eq 0 ]; then
              echo "✅ Producer output is valid"
            else
              echo "❌ Producer output violates contract"
              exit 1
            fi
          '';

          # tool2の入力を検証
          test-consumer = pkgs.writeShellScriptBin "test-consumer" ''
            #!/usr/bin/env bash
            set -euo pipefail
            
            if [ $# -lt 2 ]; then
              echo "Usage: test-consumer <schema.json> <test-data.json>"
              echo "Example: test-consumer log-schema.json sample-log.json"
              exit 1
            fi
            
            schema="$1"
            testdata="$2"
            
            echo "Validating test data against schema: $schema"
            
            # テストデータを検証
            ${pkgs.nodePackages.ajv-cli}/bin/ajv validate -s "$schema" -d "$testdata"
            
            if [ $? -eq 0 ]; then
              echo "✅ Test data is valid for consumer"
            else
              echo "❌ Test data violates contract"
              exit 1
            fi
          '';

          # 契約テストのランナー
          contract-test = pkgs.writeShellScriptBin "contract-test" ''
            #!/usr/bin/env bash
            set -euo pipefail
            
            if [ $# -lt 3 ]; then
              echo "Usage: contract-test <schema.json> <producer-cmd> <consumer-cmd>"
              echo "Example: contract-test log-schema.json './logger' './log-processor'"
              exit 1
            fi
            
            schema="$1"
            producer="$2"
            consumer="$3"
            
            echo "=== Contract Test ==="
            echo "Schema: $schema"
            echo "Producer: $producer"
            echo "Consumer: $consumer"
            echo ""
            
            # 一時ファイル作成
            tmpfile=$(mktemp)
            
            # Step 1: Producer出力を取得して検証
            echo "Step 1: Testing producer output..."
            $producer > "$tmpfile"
            
            if ${pkgs.nodePackages.ajv-cli}/bin/ajv validate -s "$schema" -d "$tmpfile" > /dev/null 2>&1; then
              echo "✅ Producer output is valid"
            else
              echo "❌ Producer output violates contract:"
              ${pkgs.nodePackages.ajv-cli}/bin/ajv validate -s "$schema" -d "$tmpfile"
              rm "$tmpfile"
              exit 1
            fi
            
            # Step 2: ConsumerがProducer出力を処理できるか
            echo ""
            echo "Step 2: Testing consumer with producer output..."
            if cat "$tmpfile" | $consumer > /dev/null 2>&1; then
              echo "✅ Consumer successfully processed producer output"
            else
              echo "❌ Consumer failed to process producer output"
              rm "$tmpfile"
              exit 1
            fi
            
            rm "$tmpfile"
            echo ""
            echo "✅ Contract test passed!"
          '';

          # サンプルツール: producer
          sample-producer = pkgs.writeShellScriptBin "sample-producer" ''
            #!/usr/bin/env bash
            cat << EOF
            {
              "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
              "level": "INFO",
              "message": "Sample log message",
              "context": {
                "user": {
                  "id": "user123",
                  "role": "admin"
                },
                "request": {
                  "id": "req456",
                  "path": "/api/test"
                }
              }
            }
            EOF
          '';

          # サンプルツール: consumer
          sample-consumer = pkgs.writeShellScriptBin "sample-consumer" ''
            #!/usr/bin/env bash
            # 入力JSONを読み込んで処理
            input=$(cat)
            
            # 必須フィールドの存在確認
            if ! echo "$input" | ${pkgs.jq}/bin/jq -e '.message' > /dev/null; then
              echo "Error: message field is required" >&2
              exit 1
            fi
            
            # 処理結果を出力
            echo "$input" | ${pkgs.jq}/bin/jq '{
              processed_at: now | strftime("%Y-%m-%dT%H:%M:%SZ"),
              original_message: .message,
              level: .level
            }'
          '';

          default = pkgs.writeShellScriptBin "show-readme" ''
            #!/usr/bin/env bash
            cat ${./README.md}
          '';
          
          # テスト実行
          run-tests = pkgs.writeShellScriptBin "run-tests" ''
            #!/usr/bin/env bash
            set -euo pipefail
            
            echo "=== Running Contract Testing Use Cases ==="
            echo ""
            
            # 一時ディレクトリでテスト実行（書き込み権限のため）
            tmpdir=$(mktemp -d)
            trap "rm -rf $tmpdir" EXIT
            
            # ファイルをコピー
            cp -r ${./.}/* "$tmpdir/"
            cd "$tmpdir"
            
            # pytest実行
            ${pkgs.python3.withPackages (ps: with ps; [pytest])}/bin/pytest test_contract.py -v
          '';
          
          # LLM-first entry point
          entry-run = pkgs.writeShellScriptBin "entry-run" ''
            #!/usr/bin/env ${pkgs.python3}/bin/python3
            import json
            import sys
            import subprocess
            import tempfile
            import os
            
            def process_contract_test(data):
                """Process contract testing operations from JSON input."""
                if isinstance(data, dict):
                    operations = [data]
                else:
                    operations = data
                
                for op in operations:
                    op_type = op.get("type", op.get("operation", "contract_test"))
                    
                    if op_type == "validate_producer":
                        schema = op["schema"]
                        producer_cmd = op["producer"]
                        
                        # Save schema to temp file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                            json.dump(schema, f)
                            schema_file = f.name
                        
                        try:
                            result = subprocess.run(
                                ["${self.packages.${system}.test-producer}/bin/test-producer", 
                                 schema_file, producer_cmd],
                                capture_output=True,
                                text=True
                            )
                            print(result.stdout)
                            if result.stderr:
                                print(result.stderr, file=sys.stderr)
                        finally:
                            os.unlink(schema_file)
                    
                    elif op_type == "contract_test":
                        schema = op["schema"]
                        producer = op["producer"]
                        consumer = op["consumer"]
                        
                        # Save schema
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                            json.dump(schema, f)
                            schema_file = f.name
                        
                        try:
                            result = subprocess.run(
                                ["${self.packages.${system}.contract-test}/bin/contract-test",
                                 schema_file, producer, consumer],
                                capture_output=True,
                                text=True
                            )
                            print(result.stdout)
                            if result.stderr:
                                print(result.stderr, file=sys.stderr)
                        finally:
                            os.unlink(schema_file)
                    
                    else:
                        print(f"Unknown operation: {op_type}", file=sys.stderr)
                        sys.exit(1)
            
            if __name__ == "__main__":
                try:
                    # Read JSON from stdin
                    data = json.load(sys.stdin)
                    process_contract_test(data)
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON input: {e}", file=sys.stderr)
                    print("\nExpected format:", file=sys.stderr)
                    print(json.dumps({
                        "type": "contract_test",
                        "schema": {"type": "object", "required": ["message"]},
                        "producer": "./my-logger",
                        "consumer": "./log-processor"
                    }, indent=2), file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f"Error: {e}", file=sys.stderr)
                    sys.exit(1)
          '';
        };

        # テスト用スキーマ（デモンストレーション目的）
        lib = {
          testSchema = pkgs.writeTextFile {
            name = "test-schema.json";
            text = ''
              {
                "_comment": "This is a TEST SCHEMA for demonstration purposes only",
                "_note": "Each tool should define its own production schema",
              '' + builtins.toJSON {
              "$schema" = "http://json-schema.org/draft-07/schema#";
              type = "object";
              required = ["timestamp" "level" "message"];
              properties = {
                timestamp = {
                  type = "string";
                  format = "date-time";
                };
                level = {
                  type = "string";
                  enum = ["DEBUG" "INFO" "WARN" "ERROR"];
                };
                message = {
                  type = "string";
                };
                context = {
                  type = "object";
                  properties = {
                    user = {
                      type = "object";
                      required = ["id"];
                      properties = {
                        id = { type = "string"; };
                        role = {
                          type = "string";
                          enum = ["admin" "user" "guest"];
                        };
                      };
                    };
                    request = {
                      type = "object";
                      properties = {
                        id = { type = "string"; };
                        path = { type = "string"; };
                      };
                    };
                  };
                };
              };
            } + ''
              }
            '';
        };

        # Apps for nix run
        apps = {
          default = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/show-readme";
          };
          
          run = {
            type = "app";
            program = "${self.packages.${system}.entry-run}/bin/entry-run";
          };
          
          test = {
            type = "app";
            program = "${self.packages.${system}.run-tests}/bin/run-tests";
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs
            nodePackages.ajv-cli
            jq
            python3
            python3Packages.pytest
          ];

          shellHook = ''
            echo "Contract Testing Environment"
            echo "Available commands:"
            echo "  - test-producer: Validate tool output against schema"
            echo "  - test-consumer: Validate test data for consumer"
            echo "  - contract-test: Full contract test between tools"
            echo ""
            echo "Sample tools:"
            echo "  - sample-producer: Generate sample log entry"
            echo "  - sample-consumer: Process log entry"
            echo ""
            echo "Example workflow:"
            echo "  1. Create test schema: cp ${self.lib.${system}.testSchema} test-schema.json"
            echo "  2. Test producer: test-producer test-schema.json sample-producer"
            echo "  3. Full test: contract-test test-schema.json sample-producer sample-consumer"
            echo ""
            echo "Note: Each tool should define its own production schema."
            echo "      The test-schema.json is for demonstration purposes only."
          '';
        };
      }
    );
}