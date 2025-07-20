{
  description = "Search and switch to flake.nix directories";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    
    # README表示用のエントリポイント
    readmeScript = pkgs.writeShellScriptBin "search-flakes-readme" ''
      ${pkgs.coreutils}/bin/cat << 'EOF'
# flake.nix検索ツール

## 責務
指定ディレクトリ配下のflake.nixをfzf探索可能にする

## 実行
nix run .#run
EOF
    '';
    
    # メイン検索機能
    searchScript = pkgs.writeShellScriptBin "search-flakes" ''
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
    
    # JSON入力対応の実行スクリプト
    runScript = pkgs.writeShellScriptBin "search-flakes-run" ''
      # JSON入力があるか確認
      if [ ! -t 0 ]; then
        # パイプまたはリダイレクトからの入力
        input=$(${pkgs.coreutils}/bin/cat)
        if [ -n "$input" ]; then
          # JSON解析してsearch_dirを取得
          search_dir=$(echo "$input" | ${pkgs.jq}/bin/jq -r '.search_dir // empty' 2>/dev/null)
          if [ -n "$search_dir" ]; then
            # 指定ディレクトリで検索
            files=$(${pkgs.fd}/bin/fd -H -t f "flake.nix" "$search_dir" 2>/dev/null || true)
          else
            # デフォルト検索
            files=$(${pkgs.fd}/bin/fd -H -t f "flake.nix" "$HOME" 2>/dev/null || true)
          fi
        fi
      else
        # 通常実行
        files=$(${pkgs.fd}/bin/fd -H -t f "flake.nix" "$HOME" 2>/dev/null || true)
      fi
      
      if [ -z "$files" ]; then
        echo "No flake.nix files found" >&2
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
    
  in {
    packages.${system} = {
      default = readmeScript;
      readme = readmeScript;
      search-flakes = searchScript;
      run = runScript;
    };

    apps.${system} = {
      default = {
        type = "app";
        program = "${readmeScript}/bin/search-flakes-readme";
      };
      
      run = {
        type = "app";
        program = "${runScript}/bin/search-flakes-run";
      };
    };
  };
}