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
      
      # The modular scripts
      select-project = pkgs.writeShellApplication {
        name = "select-project";
        runtimeInputs = with pkgs; [
          findutils
          coreutils
          gnugrep
          bash
          fzf
        ];
        text = builtins.replaceStrings 
          ["#!/usr/bin/env bash"] 
          [""] 
          (builtins.readFile ./scripts/select-project);
      };
      
      launch-claude = pkgs.writeShellApplication {
        name = "launch-claude";
        runtimeInputs = with pkgs; [
          coreutils
          bash
        ];
        text = builtins.replaceStrings 
          ["#!/usr/bin/env bash"] 
          [""] 
          (builtins.readFile ./scripts/launch-claude);
      };
      
      claude-launcher = pkgs.writeShellApplication {
        name = "claude-launcher";
        runtimeInputs = with pkgs; [
          self.packages.${system}.select-project
          self.packages.${system}.launch-claude
        ];
        text = ''
          # Main launcher using modular scripts
          project_dir=$(${self.packages.${system}.select-project}/bin/select-project) || exit 1
          
          # Determine if we should try --continue mode
          if [[ -d "$project_dir/.claude" ]]; then
            # Project might have conversation history
            ${self.packages.${system}.launch-claude}/bin/launch-claude "$project_dir" --continue
          else
            # New project or no history
            ${self.packages.${system}.launch-claude}/bin/launch-claude "$project_dir"
          fi
        '';
      };
    };
    
    apps.${system} = {
      default = {
        type = "app";
        program = "${self.packages.${system}.claude-launcher}/bin/claude-launcher";
      };
      
      test = {
        type = "app";
        program = let
          testScript = pkgs.writeText "test_e2e_integrated.bats" (builtins.readFile ./test_e2e_integrated.bats);
        in "${pkgs.writeShellScript "run-tests" ''
          echo "Running Claude launcher e2e tests..."
          ${pkgs.bats}/bin/bats ${testScript}
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
    } ''
      echo "Running Claude launcher e2e tests..."
      # Copy test script
      cp ${./test_e2e_integrated.bats} test_e2e_integrated.bats
      chmod +x test_e2e_integrated.bats
      
      # Run tests
      ${pkgs.bats}/bin/bats test_e2e_integrated.bats
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
