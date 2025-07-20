{
  description = "Search and switch to flake.nix directories";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    packages.${system}.default = pkgs.writeShellScriptBin "search-flakes" ''
      # flake.nixファイルを検索してfzfで選択
      files=$(${pkgs.fd}/bin/fd -H -t f "flake.nix" "$HOME" 2>/dev/null || true)
      
      if [ -z "$files" ]; then
        echo "No flake.nix files found in $HOME" >&2
        exit 1
      fi
      
      selected_dir=$(echo "$files" | 
        while read -r file; do ${pkgs.coreutils}/bin/dirname "$file"; done | 
        ${pkgs.coreutils}/bin/sort -u |
        ${pkgs.fzf}/bin/fzf --reverse --header="Select flake directory:" \
          --preview '${pkgs.eza}/bin/eza -la --color=always {}' \
          --preview-window=right:50%)
      
      if [ -n "$selected_dir" ]; then
        echo "$selected_dir"
      else
        exit 1
      fi
    '';

    apps.${system}.default = {
      type = "app";
      program = "${self.packages.${system}.default}/bin/search-flakes";
    };
  };
}