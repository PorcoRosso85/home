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
      # 履歴ファイルから直接読み込む
      if [ -f ~/.bash_history ]; then
        tac ~/.bash_history | 
        awk '!seen[$0]++' | 
        ${pkgs.fzf}/bin/fzf --height ''${FZF_TMUX_HEIGHT:-40%} $FZF_DEFAULT_OPTS -n2..,.. --tiebreak=index --bind=ctrl-r:toggle-sort $FZF_CTRL_R_OPTS --query="$READLINE_LINE" +m
      else
        echo "No bash history file found" >&2
        exit 1
      fi
    '';

    apps.${system}.default = {
      type = "app";
      program = "${self.packages.${system}.default}/bin/search-bash-histories";
    };
  };
}