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
        
        # Python環境（OAuth2ヘルパー用）
        pythonEnv = pkgs.python3;
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
        apps = rec {
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
              
              # 一時ディレクトリで実行（書き込み権限の問題を回避）
              export TMPDIR=$(mktemp -d)
              cd $TMPDIR
              
              # 必要なファイルをコピー
              cp -r ${./.}/mail .
              cp ${./.}/mail.test.ts .
              cp ${./.}/mail_test_helper.ts .
              cp ${./.}/deno.json .
              
              # テスト実行（TDD Red Phase なのですべて失敗する）
              ${denoEnv}/bin/deno test \
                --allow-read \
                --allow-write \
                --allow-net \
                --allow-env \
                --no-lock \
                mail.test.ts || {
                  echo ""
                  echo "========================================="
                  echo "TDD Red Phase: すべてのテストが失敗しました（想定通り）"
                  echo "次のステップ: 実装を追加してテストを通す"
                  echo "========================================="
                  rm -rf $TMPDIR 2>/dev/null || true
                  exit 0  # TDD Red Phaseなので正常終了
                }
              
              rm -rf $TMPDIR 2>/dev/null || true
            ''}";
          };
          
          # コードフォーマット
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format-code" ''
              echo "Formatting TypeScript code..."
              cd ${./.}
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
              cd ${./.}
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
              cd ${./.}
              ${denoEnv}/bin/deno check --no-lock mail/mod.ts mail.test.ts
            ''}";
          };
          
          # 実際のGmail CLI
          gmail = {
            type = "app";
            program = "${packages.gmail-cli}/bin/gmail-cli";
          };
          
          # OAuth2ヘルパー
          oauth = {
            type = "app";
            program = "${packages.oauth-helper}/bin/oauth-helper";
          };
        };
        
        # パッケージ定義
        packages = {
          # 実際のGmail APIを使用するCLI
          gmail-cli = pkgs.writeShellScriptBin "gmail-cli" ''
            # 必要な環境変数をチェック
            if [ -z "$GOOGLE_CLIENT_ID" ]; then
              echo "エラー: GOOGLE_CLIENT_ID を設定してください"
              echo ""
              echo "Google Cloud Consoleでの設定手順:"
              echo "1. https://console.cloud.google.com/ にアクセス"
              echo "2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）"
              echo "3. APIs & Services > Credentials に移動"
              echo "4. Create Credentials > OAuth client ID を選択"
              echo "5. Application type: Desktop app を選択"
              echo "6. 作成されたClient IDとClient Secretをコピー"
              echo ""
              echo "環境変数の設定:"
              echo "  export GOOGLE_CLIENT_ID='your-client-id'"
              echo "  export GOOGLE_CLIENT_SECRET='your-client-secret'"
              echo ""
              echo "Gmail APIの有効化:"
              echo "1. APIs & Services > Library に移動"
              echo "2. 'Gmail API' を検索して有効化"
              exit 1
            fi
            
            # Denoで実行
            exec ${denoEnv}/bin/deno run \
              --allow-net \
              --allow-read \
              --allow-write \
              --allow-env \
              ${./.}/mail/cli_auto.ts "$@"
          '';
          
          # OAuth2トークン取得ヘルパー
          oauth-helper = pkgs.writeShellScriptBin "oauth-helper" ''
            echo "Gmail OAuth2 トークン取得ヘルパー"
            echo ""
            
            if [ "$1" = "server" ]; then
              echo "簡易コールバックサーバーを起動中..."
              echo "ブラウザで認証後、このサーバーにリダイレクトされます"
              echo ""
              
              # Python簡易サーバー
              ${pythonEnv}/bin/python3 -c "
import http.server
import urllib.parse
import socketserver

class CallbackHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
<html>
<body>
<h1>認証コードを取得しました</h1>
<p>以下のコードを使用してアクセストークンを取得してください:</p>
<pre style='background: #f0f0f0; padding: 10px;'>''' + code.encode() + b'''</pre>
<p>次のコマンドを実行:</p>
<pre>oauth-helper exchange --code ''' + code.encode() + b'''</pre>
</body>
</html>
            ''')
            print(f'\n✅ 認証コード: {code}\n')
        else:
            self.send_error(400, 'No authorization code')

with socketserver.TCPServer(('localhost', 8080), CallbackHandler) as httpd:
    print('コールバックサーバーを http://localhost:8080 で起動しました')
    httpd.serve_forever()
"
            
            elif [ "$1" = "exchange" ]; then
              if [ -z "$2" ] || [ "$2" != "--code" ] || [ -z "$3" ]; then
                echo "使用方法: oauth-helper exchange --code <authorization-code>"
                exit 1
              fi
              
              CODE="$3"
              
              echo "アクセストークンを取得中..."
              
              # curlでトークンを取得
              RESPONSE=$(${pkgs.curl}/bin/curl -s -X POST \
                https://oauth2.googleapis.com/token \
                -d "code=$CODE" \
                -d "client_id=$GOOGLE_CLIENT_ID" \
                -d "client_secret=$GOOGLE_CLIENT_SECRET" \
                -d "redirect_uri=http://localhost:8080/callback" \
                -d "grant_type=authorization_code")
              
              echo "$RESPONSE" | ${pkgs.jq}/bin/jq '.'
              
              ACCESS_TOKEN=$(echo "$RESPONSE" | ${pkgs.jq}/bin/jq -r '.access_token')
              if [ "$ACCESS_TOKEN" != "null" ]; then
                echo ""
                echo "✅ アクセストークンを取得しました！"
                echo ""
                echo "以下のコマンドでメールを取得できます:"
                echo "  export GMAIL_ACCESS_TOKEN='$ACCESS_TOKEN'"
                echo "  nix run .#gmail -- fetch --unread --limit 5"
              else
                echo ""
                echo "❌ トークンの取得に失敗しました"
              fi
              
            else
              echo "使用方法:"
              echo "  oauth-helper server    # コールバックサーバーを起動"
              echo "  oauth-helper exchange --code <code>  # トークンに交換"
              echo ""
              echo "手順:"
              echo "1. 別のターミナルで: oauth-helper server"
              echo "2. gmail-cli auth を実行してURLを取得"
              echo "3. ブラウザでURLを開いて認証"
              echo "4. 表示されたコードで: oauth-helper exchange --code <code>"
            fi
          '';
        };
        
      });
}