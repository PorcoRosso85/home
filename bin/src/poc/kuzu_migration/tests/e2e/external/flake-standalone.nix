{
  description = "Standalone example of using kuzu-migrate library functions";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    # In a real project, you would use:
    # kuzu-migrate.url = "github:your-org/kuzu-migrate";
    # Or for local development:
    # kuzu-migrate.url = "path:/path/to/kuzu-migrate";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # This demonstrates the expected library interface
        # In a real scenario, you would use: kuzu-migrate.lib.mkKuzuMigration
        mkKuzuMigration = { pkgs, ddlPath ? "./ddl" }: {
          migrate = {
            type = "app";
            program = "${pkgs.writeShellScript "migrate" ''
              echo "Would run: kuzu-migrate --ddl ${ddlPath} apply"
            ''}";
          };
          
          init = {
            type = "app";
            program = "${pkgs.writeShellScript "init" ''
              echo "Would run: kuzu-migrate --ddl ${ddlPath} init"
            ''}";
          };
          
          status = {
            type = "app";
            program = "${pkgs.writeShellScript "status" ''
              echo "Would run: kuzu-migrate --ddl ${ddlPath} status"
            ''}";
          };
          
          snapshot = {
            type = "app";
            program = "${pkgs.writeShellScript "snapshot" ''
              echo "Would run: kuzu-migrate --ddl ${ddlPath} snapshot"
            ''}";
          };
        };
        
        # Use the library function
        migrationApps = mkKuzuMigration {
          inherit pkgs;
          ddlPath = "./custom_ddl";
        };
      in
      {
        # Export the migration apps
        apps = migrationApps // {
          # Additional custom apps
          show-interface = {
            type = "app";
            program = "${pkgs.writeShellScript "show-interface" ''
              echo "This flake demonstrates the kuzu-migrate library interface"
              echo "=========================================================="
              echo ""
              echo "The lib.mkKuzuMigration function accepts:"
              echo "  - pkgs: The nixpkgs package set"
              echo "  - ddlPath: Path to DDL directory (default: ./ddl)"
              echo ""
              echo "It returns these apps:"
              echo "  - init: Initialize migration state"
              echo "  - status: Check migration status"
              echo "  - migrate: Apply pending migrations"
              echo "  - snapshot: Create schema snapshot"
              echo ""
              echo "Each app respects the ddlPath parameter."
            ''}";
          };
        };
        
        # Example of a package that uses kuzu-migrate
        packages.my-database-app = pkgs.stdenv.mkDerivation {
          pname = "my-database-app";
          version = "1.0.0";
          
          src = ./.;
          
          # In a real scenario, you would add kuzu-migrate as a build input:
          # buildInputs = [ kuzu-migrate.packages.${system}.default ];
          
          installPhase = ''
            mkdir -p $out/bin
            
            cat > $out/bin/my-database-app << 'EOF'
            #!/usr/bin/env bash
            echo "My application that uses KuzuDB with migrations"
            echo "Would use kuzu-migrate for schema management"
            EOF
            
            chmod +x $out/bin/my-database-app
          '';
        };
      });
}