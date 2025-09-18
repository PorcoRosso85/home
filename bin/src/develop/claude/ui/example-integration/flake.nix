{
  description = "Example project using Claude UI as a flake dependency";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    # Local path for testing - replace with GitHub URL in production
    claude-ui.url = "path:/home/nixos/bin/src/develop/claude/ui";
    # For production use:
    # claude-ui.url = "github:yourusername/claude-ui";
  };

  outputs = { self, nixpkgs, flake-utils, claude-ui }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Method 1: Development shell with Claude UI integrated
        devShells.default = pkgs.mkShell {
          packages = [
            # Include Claude CLI from the flake dependency
            claude-ui.packages.${system}.claude-cli
            # Your project's other dependencies
            pkgs.nodejs_20
            pkgs.git
          ];
          
          shellHook = ''
            echo "🚀 Example Project with Claude UI Integration"
            echo ""
            echo "Available commands:"
            echo "  claude             - Launch Claude Code in current directory"
            echo "  claude --flake     - Select project with fzf"
            echo "  claude /path/dir   - Launch in specific directory"
            echo ""
            echo "This development shell includes Claude UI as a flake dependency."
          '';
        };
        
        # Method 2: Custom wrapper packages
        packages = {
          # Simple wrapper that adds project-specific configuration
          my-claude = pkgs.writeShellApplication {
            name = "my-claude";
            runtimeInputs = [ claude-ui.packages.${system}.claude-cli ];
            text = ''
              # Add any project-specific setup here
              echo "🔧 Launching Claude with project-specific configuration..."
              
              # Example: Set project-specific environment variables
              export PROJECT_ROOT="${toString ./.}"
              
              # Call the original claude command with all arguments
              claude "$@"
            '';
          };
          
          # Specialized launcher for this project
          project-launcher = pkgs.writeShellApplication {
            name = "project-launcher";
            runtimeInputs = [ 
              claude-ui.packages.${system}.select-project
              claude-ui.packages.${system}.launch-claude
            ];
            text = ''
              # Custom workflow using individual components
              echo "📂 Custom project launcher"
              
              # Use project selector with custom root
              PROJECT=$(claude-select-project --root "${toString ./.}")
              
              # Launch with project-specific logic
              if [[ -f "$PROJECT/flake.nix" ]]; then
                echo "✅ Launching in Nix project: $PROJECT"
                claude-launch "$PROJECT" --continue
              else
                echo "📝 Launching in regular project: $PROJECT"
                claude-launch "$PROJECT"
              fi
            '';
          };
        };
      });
}