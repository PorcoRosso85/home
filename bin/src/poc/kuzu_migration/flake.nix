{
  description = "A development environment for the kuzu_migration project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python environment with all test dependencies
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          # Core dependencies
          kuzu
          # Test dependencies
          pytest
          pytest-cov
          pytest-timeout
          pytest-mock
          pytest-xdist
          pytest-asyncio
          # Additional useful test utilities
          pytest-benchmark
          pytest-env
          pytest-html
          pytest-sugar  # Better test output formatting
          # pytest-clarity  # Better assertion diffs (not available in nixpkgs)
          hypothesis
        ]);
        
        kuzu-migrate = pkgs.writeShellApplication {
          name = "kuzu-migrate";
          runtimeInputs = with pkgs; [ kuzu coreutils ];
          text = builtins.readFile ./src/kuzu-migrate.sh;
        };
      in
      {
        packages.default = kuzu-migrate;
        
        devShells.default = pkgs.mkShell {
          # The Nix packages available in the development environment
          packages = with pkgs; [
            pythonEnv # Python environment with all dependencies
            ruff
            uv # For managing python dependencies
            # C++ runtime libraries for kuzu
            stdenv.cc.cc.lib
            deno # Add deno for causal_with_migration tests
            nodejs_20
            nodePackages.typescript
            # Add kuzu-migrate to development environment
            kuzu-migrate
          ];
          
          # Automatically set library paths for KuzuDB
          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
          
          shellHook = ''
            echo "KuzuDB Migration CLI Development Environment"
            echo "kuzu-migrate: v$(kuzu-migrate --version | cut -d' ' -f2)"
            echo ""
            echo "Commands:"
            echo "  kuzu-migrate --help        - Show CLI help"
            echo "  nix run .#kuzu-migrate     - Run the CLI"
            echo "  nix build                  - Build the package"
            echo ""
            echo "Test Commands:"
            echo "  nix run .#test             - Run all tests (internal + external E2E)"
            echo "  nix run .#test-cov         - Run tests with coverage report"
            echo "  nix run .#test-unit        - Run unit tests only"
            echo "  nix run .#test-integration - Run integration tests only"
            echo "  nix run .#test-internal    - Run internal E2E tests"
            echo "  nix run .#test-external    - Run external E2E tests"
            echo "  nix run .#test-causal      - Run causal migration tests"
            echo ""
            echo "Other Commands:"
            echo "  nix run .#example          - Run example usage"
            echo ""
            echo "Python test environment includes:"
            echo "  - pytest with plugins: cov, timeout, mock, xdist, asyncio"
            echo "  - hypothesis for property-based testing"
            echo "  - All dependencies in clean Nix environment"
          '';
        };
        
        # Applications
        apps = {
          # Default app
          default = self.apps.${system}.kuzu-migrate;
          
          # Main kuzu-migrate CLI
          kuzu-migrate = {
            type = "app";
            program = "${kuzu-migrate}/bin/kuzu-migrate";
          };
          
          # Test runner
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              
              echo "🧪 Running KuzuDB Migration tests..."
              echo "=============================="
              echo ""
              
              # Check if tests directory exists
              if [ ! -d "tests" ]; then
                echo "⚠️  Warning: No 'tests' directory found in current location!"
                echo "Current directory: $(pwd)"
                echo ""
                echo "Looking for test files in the project..."
              fi
              
              # Check for pytest.ini to ensure we're in the right place
              if [ -f "tests/pytest.ini" ]; then
                echo "✅ Found pytest configuration at tests/pytest.ini"
                cd tests
              elif [ -f "pytest.ini" ]; then
                echo "✅ Found pytest configuration at pytest.ini"
              else
                echo "⚠️  Warning: No pytest.ini found. Tests may not run with proper configuration."
              fi
              
              echo ""
              echo "🔍 Discovering tests..."
              
              # Count test files
              INTERNAL_TESTS=$(find . -path "*/e2e/internal/test_*.py" 2>/dev/null | wc -l || echo "0")
              EXTERNAL_TESTS=$(find . -path "*/e2e/external/test_*.py" 2>/dev/null | wc -l || echo "0")
              OTHER_TESTS=$(find . -name "test_*.py" -not -path "*/e2e/*" 2>/dev/null | wc -l || echo "0")
              
              echo "  Internal E2E tests: $INTERNAL_TESTS files"
              echo "  External E2E tests: $EXTERNAL_TESTS files"
              echo "  Other test files: $OTHER_TESTS files"
              
              TOTAL_TESTS=$((INTERNAL_TESTS + EXTERNAL_TESTS + OTHER_TESTS))
              
              if [ "$TOTAL_TESTS" -eq 0 ]; then
                echo ""
                echo "❌ Error: No test files found!"
                echo ""
                echo "Expected test structure:"
                echo "  tests/e2e/internal/test_*.py  - Internal E2E tests"
                echo "  tests/e2e/external/test_*.py  - External E2E tests"
                echo ""
                exit 1
              fi
              
              echo ""
              echo "📋 Running all tests (internal and external E2E)..."
              echo ""
              
              # Run pytest with proper configuration
              # If we have a pytest.ini, it will handle test discovery
              exec ${pythonEnv}/bin/pytest -v "$@"
            ''}";
          };
          
          # Run example usage
          example = {
            type = "app";
            program = "${pkgs.writeShellScript "example" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "📋 Running example usage..."
              exec ${pythonEnv}/bin/python example_usage.py "$@"
            ''}";
          };
          
          # Test with coverage
          test-cov = {
            type = "app";
            program = "${pkgs.writeShellScript "test-cov" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "🧪 Running tests with coverage..."
              exec ${pythonEnv}/bin/pytest --cov=src --cov-report=term-missing --cov-report=html "$@"
            ''}";
          };
          
          # Test only unit tests
          test-unit = {
            type = "app";
            program = "${pkgs.writeShellScript "test-unit" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "🧪 Running unit tests..."
              exec ${pythonEnv}/bin/pytest -m unit "$@"
            ''}";
          };
          
          # Test only integration tests
          test-integration = {
            type = "app";
            program = "${pkgs.writeShellScript "test-integration" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "🧪 Running integration tests..."
              exec ${pythonEnv}/bin/pytest -m integration "$@"
            ''}";
          };
          
          # Test internal e2e tests
          test-internal = {
            type = "app";
            program = "${pkgs.writeShellScript "test-internal" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "🧪 Running internal E2E tests..."
              exec ${pythonEnv}/bin/pytest tests/e2e/internal "$@"
            ''}";
          };
          
          # Test external e2e tests
          test-external = {
            type = "app";
            program = "${pkgs.writeShellScript "test-external" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "🧪 Running external E2E tests..."
              exec ${pythonEnv}/bin/pytest tests/e2e/external "$@"
            ''}";
          };
          
          # Test causal_with_migration
          test-causal = {
            type = "app";
            program = "${pkgs.writeShellScript "test-causal" ''
              cd causal_with_migration
              
              # Kill any existing servers
              ${pkgs.killall}/bin/killall deno 2>/dev/null || true
              
              # Start WebSocket server
              ${pkgs.deno}/bin/deno run --allow-net websocket-server.ts &
              SERVER_PID=$!
              
              # Wait for server startup
              sleep 2
              
              # Run tests
              ${pkgs.deno}/bin/deno test \
                --no-check \
                --allow-net \
                --v8-flags=--max-old-space-size=512 \
                --unstable \
                --trace-leaks \
                causal-sync-client.test.ts causal-ddl-integration.test.ts "$@"
              TEST_RESULT=$?
              
              # Cleanup
              kill $SERVER_PID 2>/dev/null || true
              ${pkgs.killall}/bin/killall deno 2>/dev/null || true
              
              exit $TEST_RESULT
            ''}";
          };
        };
      })
    // {
      # Library functions for other flakes to use
      lib.mkKuzuMigration = { pkgs, ddlPath ? "./ddl" }: {
        # Minimalist approach - just wrap the CLI
        init = {
          type = "app";
          program = "${self.packages.${pkgs.system}.default}/bin/kuzu-migrate --ddl ${ddlPath} init";
        };
        
        migrate = {
          type = "app";
          program = "${self.packages.${pkgs.system}.default}/bin/kuzu-migrate --ddl ${ddlPath} apply";
        };
        
        status = {
          type = "app";
          program = "${self.packages.${pkgs.system}.default}/bin/kuzu-migrate --ddl ${ddlPath} status";
        };
        
        snapshot = {
          type = "app";
          program = "${self.packages.${pkgs.system}.default}/bin/kuzu-migrate --ddl ${ddlPath} snapshot";
        };
        
        # Single responsibility: check state
        check = {
          type = "app";
          program = "${pkgs.writeShellScript "check-state" ''
            # Source minimalist functions
            source ${self.packages.${pkgs.system}.default}/share/kuzu-migrate/minimalist-cli.sh
            
            echo "=== kuzu-migrate state check ==="
            echo ""
            
            # DDL check with hints
            report_state "ddl-check" "${ddlPath}"
            
            # Add hints based on DDL state
            if [[ ! -d "${ddlPath}" ]]; then
              echo ""
              echo "→ run .#init to create DDL directory structure"
            elif [[ ! -d "${ddlPath}/migrations" ]] || [[ ! -d "${ddlPath}/snapshots" ]]; then
              echo ""
              echo "→ run .#init to complete DDL directory structure"
            fi
            
            echo ""
            report_state "environment-check"
            
            # Add hints based on environment state
            if ! command -v kuzu >/dev/null 2>&1; then
              echo ""
              echo "→ install kuzu to use migration tools"
            fi
            
            # Check for database path issues
            if [[ -n "''${KUZU_DB_PATH:-}" ]] && [[ ! -d "$(dirname "''${KUZU_DB_PATH}")" ]]; then
              echo ""
              echo "→ KUZU_DB_PATH parent directory missing: $(dirname "''${KUZU_DB_PATH}")"
            fi
          ''}";
        };
      };
    };
}