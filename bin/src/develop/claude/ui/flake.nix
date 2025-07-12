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
          bash
        ];
        text = ''
          # Debug logging
          debug_log() {
            [[ -n "$DEBUG" ]] && echo "[DEBUG] $*" >&2
          }
          
          # Normalize path: expand tilde and make absolute
          normalize_path() {
            local path="$1"
            path=$(eval echo "$path")
            [[ "$path" != /* ]] && path="$(pwd)/$path"
            echo "$path"
          }
          
          # Main
          debug_log "Starting claude launcher"
          
          # Find all flake.nix files
          files=$(find "$(pwd)" -name "flake.nix" -type f 2>/dev/null | grep -v "/.git/")
          debug_log "Found $(echo "$files" | wc -l) flake.nix files"
          
          # Run fzf selector
          result=$(echo "$files" | nix run nixpkgs#fzf -- \
            --print-query \
            --prompt="Select flake.nix or enter new project path: " \
            --preview="head -20 {}" \
            --preview-window=right:50%:wrap \
            --header=$'Enter: Confirm | Tab: Edit selection | Type path: Create new project\n─────────────────────────────────────────────────' \
            --bind='tab:replace-query' \
            || echo "")
          
          # Check if cancelled
          if [[ -z "$result" ]]; then
            echo "No selection made"
            exit 1
          fi
          
          # Parse fzf output
          query=$(echo "$result" | head -1)
          selected=$(echo "$result" | tail -n +2)
          debug_log "Query: '$query', Selected: '$selected'"
          
          # Determine mode and launch
          if [[ -z "$selected" && -n "$query" ]]; then
            # New project mode
            target_dir=$(normalize_path "$query")
            debug_log "New project mode: $target_dir"
            
            echo "Creating new project at: $target_dir"
            mkdir -p "$target_dir" || {
              echo "Error: Failed to create directory $target_dir"
              exit 1
            }
            cd "$target_dir"
            exec env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions
          elif [[ -n "$selected" ]]; then
            # Existing project mode
            target_dir=$(dirname "$selected")
            debug_log "Existing project mode: $target_dir"
            
            echo "Launching Claude in: $target_dir"
            cd "$target_dir"
            
            # Try with conversation history first
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
