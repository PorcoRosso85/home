{
  description = "Bash development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # パッケージ中心設計：ツールセットをpackages.defaultに集約
        packages.default = pkgs.buildEnv {
          name = "bash-dev-tools";
          paths = with pkgs; [
            # Bash shell
            bash
            
            # LSP server
            nodePackages.bash-language-server
            
            # Static analysis tool
            shellcheck
            
            # Testing framework
            bats
            
            # Code formatter
            shfmt
          ];
        };

        # devShellはpackages.defaultを参照（DRY原則の徹底）
        devShells.default = pkgs.mkShell {
          buildInputs = [ self.packages.${system}.default ];

          shellHook = ''
            echo "Bash development environment loaded"
            echo "Available tools:"
            echo "  - bash-language-server: LSP for Bash"
            echo "  - shellcheck: Static analysis tool"
            echo "  - bats: Bash Automated Testing System"
            echo "  - shfmt: Bash formatter"
          '';
        };

        # アプリケーション定義
        apps = {
          default = {
            type = "app";
            program = let
              # ビルド時に利用可能なアプリ名を動的に取得
              appNames = builtins.attrNames (builtins.removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                プロジェクト: Bash Development Tools
                
                利用可能なコマンド:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
                
                開発環境:
                  nix develop  - Bash開発シェル
              '';
            in "${pkgs.writeShellScript "bash-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };

          test = {
            type = "app";
            program = "${pkgs.writeShellScript "run-tests" ''
              # 現在のディレクトリで実行（flakeが存在するディレクトリ）
              
              # testsディレクトリの存在確認
              if [ ! -d "tests" ]; then
                echo "testsディレクトリが見つかりません。"
                echo "テストファイルを配置するためのディレクトリを作成してください："
                echo "  mkdir tests"
                echo "  # *.batsファイルを配置"
                exit 1
              fi
              
              # .batsファイルの存在確認
              if ! ls tests/*.bats >/dev/null 2>&1; then
                echo "testsディレクトリに*.batsファイルが見つかりません。"
                echo "batsテストファイルを作成してください："
                echo "  tests/example.bats"
                exit 1
              fi
              
              # 開発環境でbatsテストを実行
              echo "Running bats tests in development environment..."
              exec ${pkgs.nix}/bin/nix develop --command ${pkgs.bats}/bin/bats tests/*.bats "$@"
            ''}";
          };

          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              cat ${./README.md}
            ''}";
          };
        };
      });
}