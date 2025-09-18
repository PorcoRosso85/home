{
  description = "Claude Code UI - Flake-based launcher for Claude Code";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Common runtime dependencies for all scripts
        commonRuntimeInputs = with pkgs; [
          jq
          coreutils
          gnugrep
          bash
        ];
        
        # Select project script as a package
        select-project = pkgs.writeShellApplication {
          name = "claude-select-project";
          runtimeInputs = commonRuntimeInputs ++ (with pkgs; [
            fzf
            findutils
          ]);
          text = builtins.readFile ./scripts/select-project;
        };
        
        # Launch Claude script as a package
        launch-claude = pkgs.writeShellApplication {
          name = "claude-launch";
          runtimeInputs = commonRuntimeInputs;
          text = builtins.readFile ./scripts/launch-claude;
        };
        
        # Setup MCP script as a package
        setup-mcp = pkgs.writeShellApplication {
          name = "claude-setup-mcp";
          runtimeInputs = commonRuntimeInputs;
          text = ''
            #!/usr/bin/env bash
            # setup-mcp-user.sh - Set up MCP servers at user scope (one-time setup)
            #
            # This script configures MCP servers globally for all Claude Code sessions.
            # Run once after installation, then servers are available everywhere.
            
            set -euo pipefail
            
            echo "Setting up MCP servers at user scope..."
            echo "This is a one-time setup - servers will be available in all projects."
            echo
            
            # Check if claude-code is available
            # First check if it's in PATH (likely in tmux)
            if command -v claude-code >/dev/null 2>&1; then
              echo "Using claude-code from PATH"
            # Otherwise check if we can run it via nix
            elif env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --version >/dev/null 2>&1; then
              echo "Using claude-code via nix run"
            else
              echo "Error: claude-code not found. Please ensure Nix is installed and NIXPKGS_ALLOW_UNFREE=1 is set."
              echo "You can also run: nix profile install nixpkgs#claude-code --impure"
              exit 1
            fi
            
            # Function to run claude-code commands
            run_claude() {
              if command -v claude-code >/dev/null 2>&1; then
                env NIXPKGS_ALLOW_UNFREE=1 claude-code "$@"
              else
                env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- "$@"
              fi
            }
            
            # Check if already configured
            echo "Checking existing MCP servers..."
            existing_servers=$(run_claude mcp list 2>/dev/null || echo "")
            
            # Define MCP servers to configure
            # Format: ["server-name"]="command args..."
            declare -A MCP_SERVERS=(
              ["lsmcp-ts"]="/home/nixos/bin/src/develop/lsp/lsmcp/lsmcp.sh -p typescript"
              ["lsmcp-go"]="/home/nixos/bin/src/develop/lsp/lsmcp/lsmcp.sh -p gopls"
              ["lsmcp-python"]="/home/nixos/bin/src/develop/lsp/lsmcp/lsmcp.sh -p pyright"
              ["lsmcp-rust"]="/home/nixos/bin/src/develop/lsp/lsmcp/lsmcp.sh -p rust-analyzer"
              # Add more servers here:
              # ["github-mcp"]="/home/nixos/bin/src/develop/mcp/github"
              # ["filesystem-mcp"]="/home/nixos/bin/src/develop/mcp/filesystem"
            )
            
            # Configure each server
            for server_name in "''${!MCP_SERVERS[@]}"; do
              server_cmd="''${MCP_SERVERS[$server_name]}"
              
              if echo "$existing_servers" | grep -q "$server_name"; then
                echo "✓ $server_name server already configured"
              else
                echo "Adding $server_name server..."
                # Split command and arguments (using read -a for proper array assignment)
                IFS=' ' read -ra cmd_array <<< "$server_cmd"
                if run_claude mcp add "$server_name" --scope user -- "''${cmd_array[@]}"; then
                  echo "✓ $server_name server added successfully"
                else
                  echo "✗ Failed to add $server_name server"
                fi
              fi
            done
            
            echo
            echo "Setup complete! MCP servers configured:"
            run_claude mcp list
            
            echo
            echo "These servers are now available in all your Claude Code sessions."
            echo "No project-specific .mcp.json files needed!"
          '';
        };
        
        # Main CLI package that combines everything
        claude-cli = pkgs.writeShellApplication {
          name = "claude";
          runtimeInputs = commonRuntimeInputs ++ [
            select-project
            launch-claude
            setup-mcp
          ];
          text = ''
            #!/usr/bin/env bash
            # claude - Flake-based launcher for Claude Code
            # Usage:
            #   claude               # Launch in current directory
            #   claude /path/to/dir  # Launch in specified directory
            #   claude --flake       # Use fzf to select from flake.nix projects
            
            set -euo pipefail
            
            # Check if MCP servers are configured in ~/.claude.json
            # Always use nix shell to ensure jq is available (system-independent)
            if [[ -f "$HOME/.claude.json" ]]; then
              # Check if any lsmcp servers are configured using nix-provided jq
              if ! jq -e '.mcpServers | to_entries | any(.key | startswith("lsmcp"))' "$HOME/.claude.json" >/dev/null 2>&1; then
                echo "MCP servers not configured. Running setup..."
                claude-setup-mcp || {
                  echo "Setup failed. Please run claude-setup-mcp manually."
                  exit 1
                }
              fi
            else
              # First time using Claude Code
              echo "Initial setup required. Running setup..."
              claude-setup-mcp || {
                echo "Setup failed. Please run claude-setup-mcp manually."
                exit 1
              }
            fi
            
            # Parse arguments
            if [[ $# -eq 0 ]]; then
              # No arguments - use current directory
              project_dir="$(pwd)"
            elif [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
              # Show help
              echo "Usage: claude [OPTIONS] [DIRECTORY]"
              echo ""
              echo "Launch Claude Code with optional project selection."
              echo ""
              echo "Options:"
              echo "  --flake       Use fzf to select from flake.nix projects"
              echo "  --help, -h    Show this help message"
              echo ""
              echo "Arguments:"
              echo "  DIRECTORY     Launch Claude Code in specified directory"
              echo ""
              echo "Examples:"
              echo "  claude                    # Launch in current directory"
              echo "  claude ~/projects/myapp   # Launch in specific directory"
              echo "  claude --flake            # Select project with fzf"
              exit 0
            elif [[ "$1" == "--flake" ]]; then
              # --flake option - use fzf selector
              project_dir=$(claude-select-project "''${@:2}") || exit 1
            else
              # Path argument - use specified directory
              # Use nix-provided realpath for system independence
              project_dir="$(realpath "$1" 2>/dev/null)" || {
                echo "Error: Invalid path: $1"
                exit 1
              }
              if [[ ! -d "$project_dir" ]]; then
                echo "Error: Directory does not exist: $project_dir"
                exit 1
              fi
            fi
            
            # Launch Claude in the selected directory
            if [[ -f "$project_dir/flake.nix" ]]; then
              # Existing project - try to continue conversation
              claude-launch "$project_dir" --continue
            else
              # New project - start fresh
              claude-launch "$project_dir"
            fi
          '';
        };
      in
      {
        # Export individual packages for flexibility
        packages = {
          claude-cli = claude-cli;
          select-project = select-project;
          launch-claude = launch-claude;
          setup-mcp = setup-mcp;
        };
        
        # Development shell that includes the CLI
        devShells.default = pkgs.mkShell {
          packages = [ claude-cli ];
          
          shellHook = ''
            echo "Claude Code UI - Flake-based launcher"
            echo ""
            echo "Commands:"
            echo "  claude               - Launch in current directory"
            echo "  claude /path/to/dir  - Launch in specified directory"  
            echo "  claude --flake       - Select project with fzf"
            echo "  claude-setup-mcp     - Configure MCP servers"
            echo ""
            echo "Development shell activated - claude command is available directly"
          '';
        };
      });
}