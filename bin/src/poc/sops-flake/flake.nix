{
  description = "Sops-enabled application with pure Nix implementation";

  inputs = {
    # Pin specific nixpkgs version for reproducibility
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
    
    # Pin specific sops-nix version
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    
    flake-utils.url = "github:numtide/flake-utils/v1.0.0";
  };

  outputs = { self, nixpkgs, sops-nix, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Pure package definition
        packages.default = pkgs.writeShellScriptBin "sops-app" ''
          echo "Sops-app running with deterministic dependencies"
        '';
        
        # Pure encryption function (no side effects)
        packages.encrypt-pure = pkgs.writeShellApplication {
          name = "encrypt-pure";
          runtimeInputs = [ pkgs.sops ];
          text = ''
            set -euo pipefail
            
            INPUT="''${1:?Input file required}"
            OUTPUT="''${2:-$INPUT.encrypted}"
            
            if [[ ! -f "$INPUT" ]]; then
              echo "Error: Input file $INPUT not found"
              exit 1
            fi
            
            # Create new file, never modify original
            sops -e "$INPUT" > "$OUTPUT"
            echo "✅ Created encrypted file: $OUTPUT"
            echo "ℹ️  Original file unchanged: $INPUT"
          '';
        };
        
        # Development shell with fixed tools
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            sops
            age
            ssh-to-age
            gnupg
            jq
            yq
          ];
          
          shellHook = ''
            echo "sops-flake development environment"
            echo "Available commands:"
            echo "  ./scripts/init-template.sh - Initialize template"
            echo "  sops edit secrets/app.yaml - Edit encrypted secrets"
            
            # Age key detection
            if [[ -f ~/.config/sops/age/keys.txt ]]; then
              export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
              echo "✓ Age key configured: $SOPS_AGE_KEY_FILE"
            fi
            
            # SSH key detection (新規追加)
            if [[ -f ~/.ssh/id_ed25519 ]] || [[ -f ~/.ssh/id_rsa ]]; then
              echo "✓ SSH keys available for age conversion"
              echo "  Convert to age: ssh-to-age -i ~/.ssh/id_ed25519.pub"
            fi
          '';
        };
      }) // {
        # NixOS module (unchanged)
        nixosModules.default = import ./module.nix;
        
        # Templates from examples
        templates = {
          systemd = {
            path = ./examples/systemd-web-api;
            description = "SystemD service with sops-nix integration";
          };
          app = {
            path = ./examples/cli-tool;
            description = "Standalone CLI application with secrets";
          };
          script = {
            path = ./examples/deploy-script;
            description = "Encrypted shell script execution";
          };
          default = {
            path = ./examples/systemd-web-api;
            description = "SystemD service with sops-nix integration (default)";
          };
        };
      };
}
