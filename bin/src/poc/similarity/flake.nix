{
  description = "Code similarity detection tool";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    similarity = {
      url = "github:mizchi/similarity";
      flake = false;
    };
  };
  
  outputs = { self, nixpkgs, flake-utils, similarity }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        apps = {
          # 必須：README表示
          default = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "show-readme" ''
              if [ $# -ne 0 ]; then
                echo "Error: default app does not accept arguments" >&2
                echo "" >&2
              fi
              
              if [ -f ${similarity}/README.md ]; then
                ${pkgs.bat}/bin/bat -p ${similarity}/README.md
              else
                echo "README.md not found"
              fi
            ''}/bin/show-readme";
          };
          
          # Cargo経由でsimilarity-tsを実行
          ts = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "similarity-ts" ''
              export PATH="${pkgs.gcc}/bin:${pkgs.cargo}/bin:${pkgs.rustc}/bin:$PATH"
              export CARGO_HOME="''${XDG_CACHE_HOME:-$HOME/.cache}/cargo"
              export RUSTUP_HOME="''${XDG_DATA_HOME:-$HOME/.local/share}/rustup"
              
              mkdir -p "$CARGO_HOME"
              
              # 初回実行時のみインストール
              if ! command -v similarity-ts &> /dev/null; then
                echo "Installing similarity-ts..." >&2
                ${pkgs.cargo}/bin/cargo install --git https://github.com/mizchi/similarity similarity-ts
              fi
              
              exec "$CARGO_HOME/bin/similarity-ts" "$@"
            ''}/bin/similarity-ts";
          };
          
          # Python版
          py = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "similarity-py" ''
              export PATH="${pkgs.gcc}/bin:${pkgs.cargo}/bin:${pkgs.rustc}/bin:$PATH"
              export CARGO_HOME="''${XDG_CACHE_HOME:-$HOME/.cache}/cargo"
              export RUSTUP_HOME="''${XDG_DATA_HOME:-$HOME/.local/share}/rustup"
              
              mkdir -p "$CARGO_HOME"
              
              # 初回実行時のみインストール
              if ! command -v similarity-py &> /dev/null; then
                echo "Installing similarity-py..." >&2
                ${pkgs.cargo}/bin/cargo install --git https://github.com/mizchi/similarity similarity-py
              fi
              
              exec "$CARGO_HOME/bin/similarity-py" "$@"
            ''}/bin/similarity-py";
          };
          
          # Rust版
          rs = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "similarity-rs" ''
              export PATH="${pkgs.gcc}/bin:${pkgs.cargo}/bin:${pkgs.rustc}/bin:$PATH"
              export CARGO_HOME="''${XDG_CACHE_HOME:-$HOME/.cache}/cargo"
              export RUSTUP_HOME="''${XDG_DATA_HOME:-$HOME/.local/share}/rustup"
              
              mkdir -p "$CARGO_HOME"
              
              # 初回実行時のみインストール
              if ! command -v similarity-rs &> /dev/null; then
                echo "Installing similarity-rs..." >&2
                ${pkgs.cargo}/bin/cargo install --git https://github.com/mizchi/similarity similarity-rs
              fi
              
              exec "$CARGO_HOME/bin/similarity-rs" "$@"
            ''}/bin/similarity-rs";
          };
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            cargo
            rustc
            pkg-config
            openssl
          ];
          shellHook = ''
            echo "Similarity development environment"
            echo "Available commands:"
            echo "  nix run /home/nixos/bin/src/poc/similarity       # Show README"
          '';
        };
      });
}