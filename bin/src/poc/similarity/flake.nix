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
          
          # 統合アプリケーション（使用方法を案内）
          similarity = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "similarity" ''
              echo "Similarity Detection Tool"
              echo ""
              echo "Usage:"
              echo "  For TypeScript files: nix run /home/nixos/bin/src/poc/similarity#ts -- [args]"
              echo "  For Python files:     nix run /home/nixos/bin/src/poc/similarity#py -- [args]"
              echo "  For Rust files:       nix run /home/nixos/bin/src/poc/similarity#rs -- [args]"
              echo ""
              echo "Example:"
              echo "  nix run /home/nixos/bin/src/poc/similarity#ts -- ./src"
              echo ""
              echo "Run 'nix run /home/nixos/bin/src/poc/similarity#<lang> -- --help' for language-specific options"
            ''}/bin/similarity";
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
          
          # テスト実行
          test = {
            type = "app";
            program = let
              pythonEnv = pkgs.python3.withPackages (ps: with ps; [ pytest ]);
            in "${pkgs.writeShellScriptBin "run-tests" ''
              echo "Running similarity tests..."
              
              # 内部E2Eテストの実行
              if [ -d "e2e/internal" ]; then
                echo "Running internal E2E tests..."
                ${pythonEnv}/bin/pytest -v e2e/internal/
              else
                echo "⚠️  WARNING: No internal E2E tests found"
                echo "  Expected location: e2e/internal/"
              fi
              
              # 外部E2Eテストの実行
              if [ -f "e2e/external/flake.nix" ]; then
                echo "Running external E2E tests..."
                (cd e2e/external && nix run .#test)
              else
                echo "⚠️  WARNING: No external E2E tests found"
                echo "  Expected location: e2e/external/flake.nix"
              fi
            ''}/bin/run-tests";
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
            echo "  nix run /home/nixos/bin/src/poc/similarity#ts    # Run similarity-ts"
            echo "  nix run /home/nixos/bin/src/poc/similarity#py    # Run similarity-py"
            echo "  nix run /home/nixos/bin/src/poc/similarity#rs    # Run similarity-rs"
            echo "  nix run /home/nixos/bin/src/poc/similarity#test  # Run tests"
          '';
        };
      });
}