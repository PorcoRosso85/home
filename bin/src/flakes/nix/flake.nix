{
  description = "Nix開発環境";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Nix開発ツール群
        nixDevTools =
          with pkgs;
          buildEnv {
            name = "nix-dev-tools";
            paths = [
              # LSP
              nixd

              # Formatter
              nixfmt-rfc-style # nixfmt command

              # Linters
              statix
              deadnix

              # Development tools
              nix-diff
              nix-du

              # Additional tools
              nix-prefetch-git
              nix-tree
            ];
          };
      in
      {
        # フォーマッター
        formatter = pkgs.nixfmt-rfc-style;

        # パッケージ定義
        packages = {
          default = nixDevTools;
          inherit (pkgs) nixd statix deadnix;
          nixfmt = pkgs.nixfmt-rfc-style;
        };

        # 開発環境
        devShells.default = pkgs.mkShell {
          nativeBuildInputs = [ self.packages.${system}.default ];

          shellHook = ''
            echo "Nix開発環境"
            echo "利用可能なツール:"
            echo "  - nixd: Nix Language Server"
            echo "  - nixfmt: RFCスタイルコードフォーマッター (nixfmt-rfc-style)"
            echo "  - statix: Nixアンチパターン検出"
            echo "  - deadnix: 未使用コードの検出"
            echo "  - nix-diff: Nix導出の差分表示"
            echo "  - nix-du: Nixストアの使用量分析"
          '';
        };

        # アプリケーション
        apps = rec {
          default = {
            type = "app";
            meta.description = "Show available commands";
            program =
              let
                appNames = builtins.attrNames (removeAttrs self.apps.${system} [ "default" ]);
                helpText = ''
                  Nix開発環境

                  推奨コマンド:
                    nix fmt                    # フォーマット実行
                    nix flake check           # 全品質チェック実行

                  レガシーコマンド (互換性のため):
                  ${builtins.concatStringsSep "\n" (map (name: "    nix run .#${name}") appNames)}

                  詳細は README.md を参照してください。
                '';
              in
              "${pkgs.writeShellScript "show-help" ''
                cat << 'EOF'
                ${helpText}
                EOF
              ''}";
          };

          # nix fmt へのプロキシ（標準インターフェースへの移行）
          format = {
            type = "app";
            meta.description = "Format Nix files (deprecated: use nix fmt)";
            program = "${pkgs.writeShellScript "format-proxy" ''
              echo "注意: 'nix run .#format' は非推奨です。代わりに 'nix fmt <file>' を使用してください。"
              exec nix fmt "''${@:-flake.nix}"
            ''}";
          };

          # nix flake check へのプロキシ（標準インターフェースへの移行）
          check = {
            type = "app";
            meta.description = "Check code quality (deprecated: use nix flake check)";
            program = "${pkgs.writeShellScript "check-proxy" ''
              echo "注意: 'nix run .#check' は非推奨です。代わりに 'nix flake check' を使用してください。"
              exec nix flake check
            ''}";
          };

          # 個別リント実行（checks内のlintと重複回避のため簡素化）
          lint = {
            type = "app";
            meta.description = "Run linting tools (deprecated: use nix flake check)";
            program = "${pkgs.writeShellScript "lint" ''
              echo "注意: このコマンドは非推奨です。'nix flake check' または個別に 'nix build .#checks.$(nix eval --impure --expr builtins.currentSystem).lint' を使用してください。"
              echo ""
              echo "=== Statix (コード解析) ==="
              # 不要ディレクトリを除外して効率化: .git, .direnv, result*
              nix_files=$(find . -path './.git' -prune -o -path './.direnv' -prune -o -path './result*' -prune -o -name "*.nix" -type f -print)
              if [ -n "$nix_files" ]; then
                echo "$nix_files" | xargs ${pkgs.statix}/bin/statix check
              fi

              echo -e "\n=== Deadnix (未使用検出) ==="
              # 不要ディレクトリを除外して効率化: .git, .direnv, result*
              if [ -n "$nix_files" ]; then
                echo "$nix_files" | xargs ${pkgs.deadnix}/bin/deadnix --fail
              fi
            ''}";
          };

          readme = {
            type = "app";
            meta.description = "Show README content";
            program = "${pkgs.writeShellScript "show-readme" ''
              if [ -f README.md ]; then
                cat README.md
              else
                echo "README.mdが見つかりません"
              fi
            ''}";
          };
        };

        # CI/CDチェック
        checks = {
          format =
            pkgs.runCommand "format-check"
              {
                src = self;
              }
              ''
                set -euo pipefail
                echo "=== フォーマットチェック ==="
                cd "$src"

                # xargsを使った一括チェック（失敗時にスクリプト全体を失敗させる）
                # 不要ディレクトリを除外して効率化: .git, .direnv, result*
                if ! find . -path './.git' -prune -o -path './.direnv' -prune -o -path './result*' -prune -o -name "*.nix" -type f -print0 | xargs -0 -r ${pkgs.nixfmt-rfc-style}/bin/nixfmt --check; then
                  echo "フォーマットチェックが失敗しました"
                  exit 1
                fi

                mkdir -p $out && echo "フォーマットチェック完了" > $out/result
              '';

          lint =
            pkgs.runCommand "lint"
              {
                src = self;
              }
              ''
                set -euo pipefail
                echo "=== Statix (コード解析) ==="
                cd "$src"
                # 不要ディレクトリを除外して効率化: .git, .direnv, result*
                nix_files=$(find . -path './.git' -prune -o -path './.direnv' -prune -o -path './result*' -prune -o -name "*.nix" -type f -print)
                if [ -n "$nix_files" ]; then
                  if ! echo "$nix_files" | xargs ${pkgs.statix}/bin/statix check; then
                    echo "Statixチェックが失敗しました"
                    exit 1
                  fi
                fi

                echo "=== Deadnix (未使用検出) ==="
                # 不要ディレクトリを除外して効率化: .git, .direnv, result*
                if [ -n "$nix_files" ]; then
                  if ! echo "$nix_files" | xargs ${pkgs.deadnix}/bin/deadnix --fail; then
                    echo "Deadnixチェックが失敗しました"
                    exit 1
                  fi
                fi

                mkdir -p $out && echo "Lintチェック完了" > $out/result
              '';
        };
      }
    );
}
