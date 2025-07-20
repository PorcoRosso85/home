{
  description = "Bash history search with fzf";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    packages.${system}.default = pkgs.writeShellScriptBin "search-bash-histories" ''
      cat <<'EOF'
      search_bash_histories() {
        local output
        output=$(HISTTIMEFORMAT= history | 
            awk '{$1=""; print substr($0,2)}' |
            ${pkgs.fzf}/bin/fzf --height ''${FZF_TMUX_HEIGHT:-40%} $FZF_DEFAULT_OPTS -n2..,.. --tiebreak=index --bind=ctrl-r:toggle-sort $FZF_CTRL_R_OPTS --query="$READLINE_LINE" +m)
        READLINE_LINE=''${output}
        READLINE_POINT=''${#READLINE_LINE}
      }
      
      bind -x '"\C-r": search_bash_histories'
      EOF
    '';

    apps.${system}.default = {
      type = "app";
      program = "${self.packages.${system}.default}/bin/search-bash-histories";
    };
  };
}