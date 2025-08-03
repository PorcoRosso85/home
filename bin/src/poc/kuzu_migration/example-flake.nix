# Example flake.nix for projects using kuzu-migrate
{
  description = "Example project using kuzu-migrate";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-migrate.url = "github:yourorg/kuzu-migrate";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-migrate }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Import all kuzu-migrate commands with custom DDL path
        apps = kuzu-migrate.lib.mkKuzuMigration {
          inherit pkgs;
          ddlPath = "./ddl";  # Your project's DDL directory
        };
        
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            # Your project dependencies
            python3
            # kuzu-migrate will be available via nix run commands
          ];
          
          shellHook = ''
            echo "Project with KuzuDB migrations"
            echo ""
            echo "Migration commands:"
            echo "  nix run .#init      - Initialize DDL structure"
            echo "  nix run .#migrate   - Apply migrations"
            echo "  nix run .#status    - Show migration status"
            echo "  nix run .#snapshot  - Create database snapshot"
            
            # Auto-create DDL directory if it doesn't exist
            if [ ! -d "./ddl" ]; then
              echo ""
              echo "⚠️  No DDL directory found. Run 'nix run .#init' to set up migrations."
            fi
          '';
        };
      });
}