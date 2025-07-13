{
  description = "tmux development environment with 2-pane setup";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    packages.${system} = {
      default = self.packages.${system}.tmux-env;
      
      tmux-env = pkgs.writeShellApplication {
        name = "tmux-env";
        runtimeInputs = with pkgs; [
          tmux
          lazygit  
          yazi
          git
          coreutils
          bash
        ];
        text = ''
          exec ${./main.sh} "$@"
        '';
      };
    };
    
    apps.${system} = {
      default = {
        type = "app";
        program = "${self.packages.${system}.tmux-env}/bin/tmux-env";
      };
      run = {
        type = "app";
        program = "${self.packages.${system}.tmux-env}/bin/tmux-env";
      };
    };
  };
}