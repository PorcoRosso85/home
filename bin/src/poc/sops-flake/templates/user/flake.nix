{
  description = "User-executable service with NixOS integration and sops-nix";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  
  outputs = { self, nixpkgs, sops-nix }: 
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      nixosModules.default = ./module.nix;
      
      # Also provide direct package for testing
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.writeShellScriptBin "user-script" ''
            echo "User script executed"
            echo "This would normally read secrets from sops"
          '';
        });
      
      # Development shell for all systems
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              sops
              age
              ssh-to-age
              gnupg
            ];
            
            shellHook = ''
              echo "sops-flake development environment"
              echo "Available commands:"
              echo "  ./scripts/init-template.sh - Initialize template"
              echo "  ./scripts/setup-age-key.sh - Setup age key"
              echo "  ./scripts/verify-encryption.sh - Verify verification"
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
        });
    };
}