{
  description = "Minimal flake that depends on bin/src/flake-readme and requires readme.nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-readme.url = "path:../flake-readme";
  };

  outputs = { self, nixpkgs, flake-readme }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: 
        f nixpkgs.legacyPackages.${system}
      );
      
      # Import readme.nix (this will fail if readme.nix doesn't exist)
      readmeData = import ./readme.nix;
    in {
      packages = forAllSystems (pkgs: {
        default = pkgs.writeText "readme-content" ''
          ${readmeData.description}
          
          Goals:
          ${nixpkgs.lib.concatMapStringsSep "\n" (g: "- ${g}") readmeData.goal}
          
          Non-Goals:
          ${nixpkgs.lib.concatMapStringsSep "\n" (ng: "- ${ng}") readmeData.nonGoal}
        '';
      });

      apps = forAllSystems (pkgs: {
        readme-check = flake-readme.apps.${pkgs.system}.readme-check;
      });

      checks = forAllSystems (pkgs: {
        readme-validation = pkgs.runCommand "readme-validation" {
          buildInputs = [ pkgs.jq ];
          DOCS_REPORT = builtins.toJSON (flake-readme.lib.docs.index { root = ./.; });
        } ''
          set -euo pipefail
          echo "Validating readme.nix dependency..."
          
          # Check that readme.nix exists and is valid
          if [ ! -f ${./readme.nix} ]; then
            echo "❌ readme.nix is required but not found"
            exit 1
          fi
          
          # Validate using flake-readme
          ERR_COUNT=$(echo "$DOCS_REPORT" | jq -r '.errorCount')
          if [ "$ERR_COUNT" != "0" ]; then
            echo "❌ readme.nix validation failed"
            echo "$DOCS_REPORT" | jq -r '.reports | to_entries[] | select(.value.errors|length>0) | "\(.key):\n" + (.value.errors | map("  - " + .) | join("\n"))'
            exit 1
          fi
          
          echo "✅ readme.nix validation passed"
          touch $out
        '';
      });

      # Template for new flake projects  
      templates = {
        default = {
          path = builtins.path {
            path = ./.;
            name = "new-flake-template";
            filter = path: type: 
              builtins.match ".*/((flake\\.lock|result(-.*)?|\\.git.*|\\.gitignore|\\.gitmodules))$" path == null;
          };
          description = "Minimal flake template with flake-readme integration";
          welcomeText = ''
            # 🚀 New Flake Project Created!
            
            You've created a new flake project with organizational standards.
            
            ## Next Steps:
            
            1. **Edit readme.nix** - Update project description and goals:
               - Update description with your project summary
               - Define specific goals and non-goals  
               - Set appropriate lifecycle and owner
            
            2. **Verify setup** - Run validation:
               ```bash
               nix run .#readme-check
               ```
            
            3. **Build and test** - Ensure everything works:
               ```bash
               nix build
               nix flake check
               ```
            
            ## 📋 Organizational Standards:
            
            This template includes:
            - ✅ flake-readme dependency (required)
            - ✅ readme.nix documentation (required)
            - ✅ Validation checks via nix flake check
            - ✅ Cross-platform support
            
            ## 🔧 Template Usage:
            
            - Local: `nix flake init -t path:/home/nixos/bin/src/poc/new-flake`
            - Registry: `nix registry add org:template path:/home/nixos/bin/src/poc/new-flake`
              Then: `nix flake init -t org:template`
            
            Happy coding! 🎉
          '';
        };
      };
    };
}