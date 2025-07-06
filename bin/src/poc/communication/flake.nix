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
        
        # Gmail実行スクリプト
        gmailApp = pkgs.writeShellScriptBin "gmail-cli" ''
          # 環境変数チェック
          if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
            echo "❌ 環境変数を設定してください:"
            echo "export GOOGLE_CLIENT_ID='your-client-id'"
            echo "export GOOGLE_CLIENT_SECRET='your-client-secret'"
            exit 1
          fi
          
          # 一時ディレクトリで実行（書き込み権限確保）
          export TMPDIR=$(mktemp -d)
          cd $TMPDIR
          
          # 必要なファイルをコピー
          cp -r ${./.}/mail $TMPDIR/
          cp ${./.}/gmail.ts $TMPDIR/ 2>/dev/null || true
          
          # トークンファイルをホームディレクトリに保存
          export TOKEN_FILE="$HOME/.gmail_tokens.json"
          
          # Denoで実行
          ${pkgs.deno}/bin/deno run \
            --allow-net \
            --allow-read \
            --allow-write \
            --allow-env \
            --allow-run \
            $TMPDIR/mail/cli_full_auto.ts "$@"
          
          # クリーンアップ
          rm -rf $TMPDIR 2>/dev/null || true
        '';
        
        # テスト実行スクリプト
        testScript = pkgs.writeShellScript "run-tests" ''
          echo "Running tests..."
          
          # 一時ディレクトリ作成
          WORK_DIR=$(mktemp -d)
          trap "chmod -R u+w $WORK_DIR 2>/dev/null; rm -rf $WORK_DIR" EXIT
          
          # ファイルをコピー（書き込み権限付き）
          cp -r ${./.}/* $WORK_DIR/
          chmod -R u+w $WORK_DIR
          cd $WORK_DIR
          
          # テスト用環境変数設定
          export GOOGLE_CLIENT_ID="test-client-id"
          export GOOGLE_CLIENT_SECRET="test-client-secret"
          
          # Denoキャッシュディレクトリ設定
          export DENO_DIR="$WORK_DIR/.deno"
          mkdir -p "$DENO_DIR"
          
          # テスト実行（--lockオプションなしで）
          ${pkgs.deno}/bin/deno test \
            --allow-all \
            --no-check \
            mail.test.ts \
            mail/**/*.test.ts
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            sqlite
          ];
          
          shellHook = ''
            echo "Communication POC 開発環境"
            echo "使用可能なコマンド:"
            echo "  deno run --allow-all ./mail/cli_full_auto.ts"
            echo "  deno test --allow-all"
          '';
        };
        
        apps = {
          # デフォルト: README表示
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              ${pkgs.coreutils}/bin/cat ${./.}/README.md
            ''}";
          };
          
          # Gmail実行
          run = {
            type = "app";
            program = "${gmailApp}/bin/gmail-cli";
          };
          
          # テスト実行
          test = {
            type = "app";
            program = "${testScript}";
          };
        };
      });
}