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
          # Phase 1: Find flake.nix files
          find_flake_files() {
            find "$(pwd)" -name "flake.nix" -type f 2>/dev/null | grep -v "/.git/"
          }
          
          # Phase 1: Run fzf selector
          run_fzf_selector() {
            local files="$1"
            echo "$files" | nix run nixpkgs#fzf -- \
              --print-query \
              --prompt="Select flake.nix or enter new project path: " \
              --preview="head -20 {}" \
              --preview-window=right:50%:wrap \
              --header=$'Enter: Confirm | Tab: Edit selection | Type path: Create new project\n─────────────────────────────────────────────────' \
              --bind='tab:replace-query' \
              || echo ""
          }
          
          # Phase 1.5: Normalize path
          normalize_path() {
            local path="$1"
            # Expand tilde
            path=$(eval echo "$path")
            # Make absolute if relative
            if [[ "$path" != /* ]]; then
              path="$(pwd)/$path"
            fi
            echo "$path"
          }
          
          # Phase 1.5: Create project directory
          create_project_dir() {
            local dir="$1"
            echo "Creating new project at: $dir"
            mkdir -p "$dir" || {
              echo "Error: Failed to create directory $dir"
              return 1
            }
          }
          
          # Phase 2: Launch Claude
          launch_claude() {
            local target_dir="$1"
            local continue_session="$2"
            
            cd "$target_dir"
            
            if [[ "$continue_session" == "true" ]]; then
              echo "Launching Claude in: $target_dir"
              # Phase 3: Try with conversation history first
              env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --continue --dangerously-skip-permissions || {
                echo "No conversation history found. Starting new session..."
                exec env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions
              }
            else
              exec env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions
            fi
          }
          
          # Main logic
          main() {
            # Phase 1: File discovery and selection
            local files
            files=$(find_flake_files)
            
            local result
            result=$(run_fzf_selector "$files")
            
            # Check if fzf was cancelled
            if [[ -z "$result" ]]; then
              echo "No selection made"
              exit 1
            fi
            
            # Parse fzf output
            local query selected
            query=$(echo "$result" | head -1)
            selected=$(echo "$result" | tail -n +2)
            
            # Phase 1.5: Path preparation and project determination
            if [[ -z "$selected" && -n "$query" ]]; then
              # New project mode - query is the path
              local target_dir
              target_dir=$(normalize_path "$query")
              
              echo "Creating new project at: $target_dir"
              create_project_dir "$target_dir" || exit 1
              # Phase 2: Launch Claude
              launch_claude "$target_dir" "false"
            elif [[ -n "$selected" ]]; then
              # Existing project mode - selected file path
              local target_dir
              target_dir=$(dirname "$selected")
              
              echo "Launching Claude in: $target_dir"
              # Phase 2: Launch Claude with continue option
              launch_claude "$target_dir" "true"
            else
              echo "No selection made"
              exit 1
            fi
          }
          
          main
        '';
      };
    };
    
    apps.${system}.default = {
      type = "app";
      program = "${self.packages.${system}.claude-launcher}/bin/claude-launcher";
    };
  };
}
