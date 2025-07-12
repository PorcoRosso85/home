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
          # Parse command line arguments
          search_dir="."
          while [[ $# -gt 0 ]]; do
            case $1 in
              --directory)
                if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                  search_dir="$2"
                  shift 2
                else
                  echo "Error: --directory requires a path argument"
                  exit 1
                fi
                ;;
              *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--directory <path>]"
                exit 1
                ;;
            esac
          done
          
          # Validate directory exists
          if [[ ! -d "$search_dir" ]]; then
            echo "Error: Directory '$search_dir' does not exist"
            exit 1
          fi
          
          # Find all flake.nix files and let user select one
          selected=$(find "$search_dir" -name "flake.nix" -type f 2>/dev/null | \
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
          exec env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --continue --dangerously-skip-permissions
        '';
      };
    };
    
    apps.${system}.default = {
      type = "app";
      program = "${self.packages.${system}.claude-launcher}/bin/claude-launcher";
    };
  };
}
