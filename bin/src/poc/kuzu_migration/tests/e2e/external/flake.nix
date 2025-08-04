{
  description = "External test flake for kuzu-migrate library functions";

  inputs = {
    # Reference the parent kuzu-migrate flake
    kuzu-migrate.url = "path:../../..";
    nixpkgs.follows = "kuzu-migrate/nixpkgs";
    flake-utils.follows = "kuzu-migrate/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-migrate }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Use lib.mkKuzuMigration from the parent flake
        migrationApps = kuzu-migrate.lib.mkKuzuMigration {
          inherit pkgs;
          ddlPath = "./test_ddl";
        };
        
        # Test data directory setup
        testDdlSetup = pkgs.writeShellScriptBin "setup-test-ddl" ''
          echo "Setting up test DDL directory..."
          mkdir -p test_ddl/migrations
          
          # Create test migration files
          cat > test_ddl/migrations/000_initial.cypher << 'EOF'
          CREATE NODE TABLE users (
            id INT64,
            username STRING,
            PRIMARY KEY (id)
          );
          EOF
          
          cat > test_ddl/migrations/001_add_email.cypher << 'EOF'
          ALTER TABLE users ADD COLUMN email STRING;
          EOF
          
          echo "Test DDL directory created with sample migrations"
        '';
      in
      {
        # Re-export the migration apps for testing
        apps = migrationApps // {
          # Add test-specific apps
          setup = {
            type = "app";
            program = "${testDdlSetup}/bin/setup-test-ddl";
          };
          
          # Integration test that uses all migration commands
          integration-test = {
            type = "app";
            program = "${pkgs.writeShellScript "integration-test" ''
              set -euo pipefail
              
              echo "🧪 Running kuzu-migrate integration test..."
              echo ""
              
              # Clean up any existing test data
              rm -rf kuzu_db test_ddl
              
              # Setup test DDL
              ${testDdlSetup}/bin/setup-test-ddl
              
              echo "📁 Test DDL structure:"
              ls -la test_ddl/migrations/
              echo ""
              
              # Test init command
              echo "1️⃣ Testing init command..."
              ${migrationApps.init.program}
              echo "✅ Init completed"
              echo ""
              
              # Test status command
              echo "2️⃣ Testing status command..."
              ${migrationApps.status.program}
              echo "✅ Status completed"
              echo ""
              
              # Test migrate command
              echo "3️⃣ Testing migrate command..."
              ${migrationApps.migrate.program}
              echo "✅ Migrate completed"
              echo ""
              
              # Test status again to see applied migrations
              echo "4️⃣ Testing status after migration..."
              ${migrationApps.status.program}
              echo "✅ Post-migration status completed"
              echo ""
              
              # Test snapshot command
              echo "5️⃣ Testing snapshot command..."
              ${migrationApps.snapshot.program}
              echo "✅ Snapshot completed"
              echo ""
              
              echo "🎉 All tests passed!"
              
              # Cleanup
              echo "🧹 Cleaning up test data..."
              rm -rf kuzu_db test_ddl
            ''}";
          };
        };
        
        # Development shell for testing
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            # Include kuzu-migrate from parent flake
            kuzu-migrate.packages.${system}.default
            # Additional test dependencies
            coreutils
            findutils
          ];
          
          shellHook = ''
            echo "kuzu-migrate External Test Environment"
            echo "======================================"
            echo ""
            echo "This flake tests kuzu-migrate as an external dependency."
            echo ""
            echo "Available commands:"
            echo "  nix run .#setup             - Set up test DDL directory"
            echo "  nix run .#init              - Initialize migration state"
            echo "  nix run .#status            - Check migration status"
            echo "  nix run .#migrate           - Apply migrations"
            echo "  nix run .#snapshot          - Create schema snapshot"
            echo "  nix run .#integration-test  - Run full integration test"
            echo ""
            echo "kuzu-migrate version: $(${kuzu-migrate.packages.${system}.default}/bin/kuzu-migrate --version)"
          '';
        };
        
        # Package that demonstrates using kuzu-migrate as a library
        packages.example-app = pkgs.stdenv.mkDerivation {
          pname = "kuzu-migrate-example";
          version = "0.1.0";
          
          src = ./.;
          
          buildInputs = [ kuzu-migrate.packages.${system}.default ];
          
          installPhase = ''
            mkdir -p $out/bin
            
            # Create a wrapper script that uses kuzu-migrate
            cat > $out/bin/example-app << EOF
            #!/usr/bin/env bash
            echo "Example application using kuzu-migrate"
            echo "======================================"
            ${kuzu-migrate.packages.${system}.default}/bin/kuzu-migrate --help
            EOF
            
            chmod +x $out/bin/example-app
          '';
        };
      });
}