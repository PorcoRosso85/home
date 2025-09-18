{
  description = "開発用ターミナル設定 - Development terminal configuration flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Shell script executables
        aa = pkgs.writeShellScriptBin "aa" ''
          ${builtins.readFile ./modules/tmux/aa.sh}
          
          # Execute the main function
          aa "$@"
        '';
        
        hly = pkgs.writeShellScriptBin "hly" ''
          ${builtins.readFile ./modules/tmux/hly.sh}
          
          # Execute the main function
          hly "$@"
        '';
        
        terminal-config = pkgs.writeShellScriptBin "terminal-config" ''
          # Set up environment variables for module sourcing
          export TERMINAL_MODULES_DIR="${self}/modules"
          export TERMINAL_CONFIG_DIR="$HOME/.config/shell"
          
          # Source the main shell configuration
          source ${self}/modules/core/main.sh
          
          echo "Terminal configuration loaded from Nix modules"
        '';
        
        test-runner = pkgs.writeShellScriptBin "test-runner" ''
          #!/usr/bin/env bash
          cd ${self}
          exec ./tests/test_main.sh "$@"
        '';

      in
      {
        # Development shell environment - nix shell専用
        devShells.default = pkgs.mkShell {
          name = "terminal-dev";
          
          buildInputs = with pkgs; [
            # Core utilities
            coreutils
            gnugrep
            gawk
            gnused
            findutils
            
            # Terminal enhancements
            less
            lesspipe
            ncurses # for tput
            libnotify # for notify-send
            
            # Development tools
            helix
            tmux
            lazygit
            yazi
            fzf
            fd
            bat
            jq
            git
            rsync
            
            # Shell environment
            bashInteractive
            bash-completion
            nodePackages.bash-language-server
            
            # Add shell script executables
            aa
            hly
            terminal-config
            test-runner
          ];
          
          shellHook = ''
            echo "🚀 Terminal development environment loaded"
            echo "Available commands: aa, hly, terminal-config, test-runner"
            echo ""
            echo "Use 'nix shell' to enter this environment"
          '';
        };
      }
    );
}