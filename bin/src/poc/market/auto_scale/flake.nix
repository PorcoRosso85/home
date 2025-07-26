{
  description = "Auto-Scale Contract Management System - POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
    kuzu-py.url = "path:/home/nixos/bin/src/persistence/kuzu_py";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, kuzu-py }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python環境をセットアップ
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          pytest
          kuzu-py.packages.${system}.kuzuPy
        ]);
        
        # プロジェクト名
        projectName = "Auto-Scale Contract Management System";
        
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
          ];
          
          shellHook = ''
            echo "Auto-Scale Contract Management System - Development Environment"
            echo "Python version: $(python --version)"
            echo ""
            echo "Available commands:"
            echo "  nix run .        - Show available apps"
            echo "  nix run .#test   - Run tests"
            echo "  nix run .#readme - Show README.md"
          '';
        };
        
        # アプリケーション定義
        apps = rec {
          # デフォルト: 利用可能なアプリ一覧を動的に表示
          default = {
            type = "app";
            program = let
              # ビルド時に利用可能なアプリ名を取得
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                Project: Auto-Scale Contract Management System
                
                Available commands:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
              '';
            in "${pkgs.writeShellScript "show-help" ''
              # 引数が指定された場合はエラー
              if [ $# -gt 0 ]; then
                echo "Error: Arguments provided to default command." >&2
                echo "" >&2
                cat << 'EOF'
              ${helpText}
              EOF
                exit 1
              fi
              
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          # テスト実行
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              # Check if we're in the source directory or need to run from current directory
              if [ -d "tests" ]; then
                # Run from current directory
                exec ${pythonEnv}/bin/pytest tests/ -v "$@"
              elif [ -d "${./.}/tests" ]; then
                # Run from nix store
                exec ${pythonEnv}/bin/pytest ${./.}/tests/ -v "$@"
              else
                echo "No tests directory found."
                exit 1
              fi
            ''}";
          };
          
          # README表示
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              if [ ! -f "${./README.md}" ]; then
                echo "README.md not found."
                exit 1
              fi
              
              # 環境変数でページャーが設定されていれば使用
              if [ -n "$PAGER" ] && command -v "$PAGER" >/dev/null 2>&1; then
                exec "$PAGER" "${./README.md}"
              # lessが利用可能なら使用
              elif command -v less >/dev/null 2>&1; then
                exec less "${./README.md}"
              # それ以外はcatで表示
              else
                exec cat "${./README.md}"
              fi
            ''}";
          };
          
          # 仕様書表示
          spec = {
            type = "app";
            program = "${pkgs.writeShellScript "show-spec" ''
              spec_file="${./docs/spec.md}"
              
              if [ ! -f "$spec_file" ]; then
                echo "Specification document (docs/spec.md) not found."
                exit 1
              fi
              
              # 環境変数でページャーが設定されていれば使用
              if [ -n "$PAGER" ] && command -v "$PAGER" >/dev/null 2>&1; then
                exec "$PAGER" "$spec_file"
              # lessが利用可能なら使用
              elif command -v less >/dev/null 2>&1; then
                exec less "$spec_file"
              # それ以外はcatで表示
              else
                exec cat "$spec_file"
              fi
            ''}";
          };
          
          # 議論内容表示
          discussion = {
            type = "app";
            program = "${pkgs.writeShellScript "show-discussion" ''
              discussion_file="${./docs/discussion.md}"
              
              if [ ! -f "$discussion_file" ]; then
                echo "Discussion document (docs/discussion.md) not found."
                exit 1
              fi
              
              # 環境変数でページャーが設定されていれば使用
              if [ -n "$PAGER" ] && command -v "$PAGER" >/dev/null 2>&1; then
                exec "$PAGER" "$discussion_file"
              # lessが利用可能なら使用
              elif command -v less >/dev/null 2>&1; then
                exec less "$discussion_file"
              # それ以外はcatで表示
              else
                exec cat "$discussion_file"
              fi
            ''}";
          };
        };
        
        # パッケージ出力
        packages = {
          default = pythonEnv;
        };
      });
}