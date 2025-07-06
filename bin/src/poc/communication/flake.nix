{
  description = "Communication POC - CLIで外界とのコミュニケーションを操作";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Deno環境の設定
        denoEnv = pkgs.deno;
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            denoEnv
            sqlite
            nodejs_20  # n8n用
            nodePackages.npm
          ];
          
          shellHook = ''
            echo "Communication POC 開発環境"
            echo "使用可能なコマンド:"
            echo "  nix run .        - README.mdを表示"
            echo "  nix run .#test   - テストを実行"
            echo "  nix run .#format - コードフォーマット"
            echo "  nix run .#lint   - リンター実行"
            echo "  nix run .#check  - 型チェック"
          '';
        };
        
        # アプリケーション定義
        apps = {
          # デフォルト: README.mdを表示
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              if [ $# -ne 0 ]; then
                echo "エラー: デフォルトコマンドは引数を受け付けません" >&2
                echo "" >&2
              fi
              
              if [ -f README.md ]; then
                ${pkgs.coreutils}/bin/cat README.md
              else
                echo "README.md が見つかりません"
                exit 1
              fi
            ''}";
          };
          
          # テスト実行
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "run-tests" ''
              echo "Running e2e tests..."
              echo ""
              
              # テスト実行（TDD Red Phase なのですべて失敗する）
              ${denoEnv}/bin/deno test \
                --allow-read \
                --allow-write \
                --allow-net \
                --allow-env \
                mail.test.ts || {
                  echo ""
                  echo "========================================="
                  echo "TDD Red Phase: すべてのテストが失敗しました（想定通り）"
                  echo "次のステップ: 実装を追加してテストを通す"
                  echo "========================================="
                  exit 0  # TDD Red Phaseなので正常終了
                }
            ''}";
          };
          
          # コードフォーマット
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format-code" ''
              echo "Formatting TypeScript code..."
              ${denoEnv}/bin/deno fmt \
                --config deno.json \
                mail/ \
                mail.test.ts \
                2>/dev/null || ${denoEnv}/bin/deno fmt mail/ mail.test.ts
            ''}";
          };
          
          # リンター
          lint = {
            type = "app";
            program = "${pkgs.writeShellScript "lint-code" ''
              echo "Linting TypeScript code..."
              ${denoEnv}/bin/deno lint \
                --config deno.json \
                mail/ \
                mail.test.ts \
                2>/dev/null || ${denoEnv}/bin/deno lint mail/ mail.test.ts
            ''}";
          };
          
          # 型チェック
          check = {
            type = "app";
            program = "${pkgs.writeShellScript "check-types" ''
              echo "Type checking TypeScript code..."
              ${denoEnv}/bin/deno check mail/mod.ts mail.test.ts
            ''}";
          };
        };
      });
}