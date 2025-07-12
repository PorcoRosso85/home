{
  description = "Claude launcher with flake.nix selection via fzf";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    packages.${system} = {
      default = self.packages.${system}.claude-launcher;
      
      claude-launcher = pkgs.writeShellApplication {
        name = "claude-launcher";
        runtimeInputs = with pkgs; [
          findutils
          coreutils
          gnugrep
        ];
        text = ''
          # Find all flake.nix files and let user select one
          selected=$(find . -name "flake.nix" -type f 2>/dev/null | \
            grep -v "/.git/" | \
            nix run nixpkgs#fzf -- --prompt="Select flake.nix to launch Claude: " \
                --preview="head -20 {}" \
                --preview-window=right:50%:wrap)
          
          if [ -z "$selected" ]; then
            echo "No flake.nix selected"
            exit 1
          fi
          
          # Get directory of selected flake.nix
          target_dir=$(dirname "$selected")
          
          echo "Launching Claude in: $target_dir"
          cd "$target_dir"
          
          # Launch Claude with required flags
          exec env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --continue --dangerously-skip-permission
        '';
      };
    };
    
    apps.${system}.default = {
      type = "app";
      program = "${self.packages.${system}.claude-launcher}/bin/claude-launcher";
    };
  };
}