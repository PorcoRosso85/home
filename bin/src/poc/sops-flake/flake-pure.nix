{
  description = "Sops-enabled application with pure Nix implementation";

  inputs = {
    # Pin specific nixpkgs version for reproducibility
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
    
    # Pin specific sops-nix version
    sops-nix = {
      url = "github:Mic92/sops-nix/0.7.1";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    
    flake-utils.url = "github:numtide/flake-utils/v1.0.0";
  };

  outputs = { self, nixpkgs, sops-nix, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        sops = sops-nix.packages.${system}.sops;
      in
      {
        # Pure package definition
        packages.default = pkgs.writeShellScriptBin "sops-app" ''
          echo "Sops-app running with deterministic dependencies"
        '';
        
        # Pure encryption function (no side effects)
        packages.encrypt-pure = pkgs.writeShellApplication {
          name = "encrypt-pure";
          runtimeInputs = [ sops ];
          text = ''
            set -euo pipefail
            
            INPUT="\${1:?Input file required}"
            OUTPUT="\${2:-\$INPUT.encrypted}"
            
            if [[ ! -f "\$INPUT" ]]; then
              echo "Error: Input file \$INPUT not found"
              exit 1
            fi
            
            # Create new file, never modify original
            sops -e "\$INPUT" > "\$OUTPUT"
            echo "✅ Created encrypted file: \$OUTPUT"
            echo "ℹ️  Original file unchanged: \$INPUT"
          '';
        };
        
        # Development shell with fixed tools
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            sops
            age
            gnupg
            jq
            yq
          ];
          
          shellHook = ''
            echo "Pure Nix development environment"
            echo "All dependencies are pinned and reproducible"
          '';
        };
      }) // {
        # NixOS module (unchanged)
        nixosModules.default = import ./module.nix;
        
        # Template functionality
        templates.default = {
          path = ./template;
          description = "Pure Nix sops-enabled application template";
        };
      };
}
