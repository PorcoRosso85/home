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
          # Find all flake.nix files and let user select one or create new project
          result=$(find "$(pwd)" -name "flake.nix" -type f 2>/dev/null | \
            grep -v "/.git/" | \
            nix run nixpkgs#fzf -- \
                --print-query \
                --prompt="Select flake.nix or enter new project path: " \
                --preview="head -20 {}" \
                --preview-window=right:50%:wrap \
                --header=$'Enter: Select | Type path: Create new project\n─────────────────────────────────────────────────')
          
          # Parse fzf output
          query=$(echo "$result" | head -1)
          selected=$(echo "$result" | tail -n +2)
          
          if [[ -z "$selected" && -n "$query" ]]; then
            # New project creation mode
            # Expand tilde and normalize path
            target_dir=$(eval echo "$query")
            target_dir=$(realpath -m "$target_dir")
            
            echo "Creating new project at: $target_dir"
            mkdir -p "$target_dir"
            cd "$target_dir"
            
            # Launch Claude without --continue for new projects
            exec env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions
          elif [[ -n "$selected" ]]; then
            # Existing project selected
            target_dir=$(dirname "$selected")
            
            echo "Launching Claude in: $target_dir"
            cd "$target_dir"
            
            # Try to launch Claude with --continue first
            env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --continue --dangerously-skip-permissions || {
              echo "No conversation history found. Starting new session..."
              exec env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions
            }
          else
            echo "No selection made"
            exit 1
          fi
        '';
      };
    };
    
    apps.${system}.default = {
      type = "app";
      program = "${self.packages.${system}.claude-launcher}/bin/claude-launcher";
    };
  };
}
