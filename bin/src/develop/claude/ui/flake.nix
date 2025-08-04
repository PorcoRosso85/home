{
  description = "Claude launcher with flake.nix selection via fzf";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    scripts.url = "path:./scripts";
  };

  outputs = { self, nixpkgs, scripts }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    packages.${system} = {
      default = self.packages.${system}.claude-launcher;
      
      
      claude-launcher = pkgs.writeShellApplication {
        name = "claude-launcher";
        runtimeInputs = with pkgs; [
          scripts.packages.${system}.select-project
          scripts.packages.${system}.launch-claude
        ];
        text = ''
          # Main launcher using modular scripts  
          project_dir=$(${scripts.packages.${system}.select-project}/bin/select-project) || exit 1
          
          # Check if this is a new project (created by select-project)
          # or an existing project (selected from list)
          # Simple heuristic: if the project has a flake.nix, it's existing
          if [[ -f "$project_dir/flake.nix" ]]; then
            # Existing project - try to continue conversation
            ${scripts.packages.${system}.launch-claude}/bin/launch-claude "$project_dir" --continue
          else
            # New project - start fresh
            ${scripts.packages.${system}.launch-claude}/bin/launch-claude "$project_dir"
          fi
        '';
      };
    };
    
    apps.${system} = rec {
      # Default app shows available commands
      default = {
        type = "app";
        program = let
          appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
          helpText = ''
            Claude Launcher - Interactive project selector for Claude Code

            Available commands:
            ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
            
            Examples:
              nix run .         # Show this help
              nix run .#core    # Launch Claude in project selector mode
              nix run .#readme  # Show README documentation
              nix run .#test    # Run tests
          '';
        in "${pkgs.writeShellScript "show-help" ''
          cat << 'EOF'
          ${helpText}
          EOF
        ''}";
      };
      
      # Core functionality - launch Claude with project selection
      core = {
        type = "app";
        program = "${self.packages.${system}.claude-launcher}/bin/claude-launcher";
      };
      
      # Search for a project and launch
      search = core;  # Alias for core
      
      # Show README
      readme = {
        type = "app";
        program = "${pkgs.writeShellScript "show-readme" ''
          # Runtime solution - look for README.md in the current directory
          readme_path="$(dirname "$(readlink -f "$0")")/../../../../README.md"
          if [[ -f "$readme_path" ]]; then
            ${pkgs.bat}/bin/bat --style=plain "$readme_path" || cat "$readme_path"
          else
            # Fallback to looking in current working directory
            if [[ -f "./README.md" ]]; then
              ${pkgs.bat}/bin/bat --style=plain "./README.md" || cat "./README.md"
            else
              echo "README.md not found"
              exit 1
            fi
          fi
        ''}";
      };
      
      # Run tests
      test = {
        type = "app";
        program = "${pkgs.writeShellScript "run-tests" ''
          echo "Running Claude launcher e2e tests..."
          # Runtime solution - look for test file relative to script location
          test_path="$(dirname "$(readlink -f "$0")")/../../../../test_e2e_integrated.bats"
          if [[ -f "$test_path" ]]; then
            ${pkgs.bats}/bin/bats "$test_path"
          else
            # Fallback to looking in current working directory
            if [[ -f "./test_e2e_integrated.bats" ]]; then
              ${pkgs.bats}/bin/bats "./test_e2e_integrated.bats"
            else
              echo "test_e2e_integrated.bats not found"
              exit 1
            fi
          fi
        ''}";
      };
    };
    
    checks.${system}.default = pkgs.runCommand "claude-launcher-tests" {
      buildInputs = [ 
        pkgs.bats 
        pkgs.bash 
        pkgs.findutils
        pkgs.coreutils
        pkgs.gnugrep
      ];
      src = ./.;
    } ''
      echo "Running Claude launcher e2e tests..."
      # Copy source directory to build environment
      cp -r $src/* .
      
      # Run tests if file exists
      if [[ -f test_e2e_integrated.bats ]]; then
        chmod +x test_e2e_integrated.bats
        ${pkgs.bats}/bin/bats test_e2e_integrated.bats
      else
        echo "Warning: test_e2e_integrated.bats not found, skipping tests"
      fi
      touch $out
    '';
    
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = with pkgs; [
        # Bash development
        bash-language-server
        shellcheck
        shfmt
        
        # Testing
        bats
      ];
      
      shellHook = ''
        echo "Bash development environment"
        echo "  - bash-language-server"
        echo "  - shellcheck"
        echo "  - shfmt"
        echo "  - bats"
      '';
    };
  };
}
