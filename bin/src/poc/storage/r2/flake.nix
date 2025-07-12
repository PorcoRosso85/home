{
  description = "Cloudflare R2 CLI環境";

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
        # テスト実行用のアプリ
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "test-runner" ''
            #!/usr/bin/env bash
            set -euo pipefail
            
            # フレークのソースディレクトリを取得
            FLAKE_DIR="${self}"
            
            # テストファイルへの絶対パス
            TEST_FILE="$FLAKE_DIR/test_flake.py"
            
            # テストファイルの存在確認
            if [ ! -f "$TEST_FILE" ]; then
              echo "Error: test_flake.py not found at $TEST_FILE"
              echo "Looking for test file in current directory..."
              if [ -f "./test_flake.py" ]; then
                TEST_FILE="./test_flake.py"
              else
                echo "Error: test_flake.py not found"
                exit 1
              fi
            fi
            
            # カレントディレクトリでテストを実行
            cd "$(dirname "$TEST_FILE")"
            exec ${pkgs.python3.withPackages (ps: with ps; [ pytest ])}/bin/pytest "$(basename "$TEST_FILE")" -v "$@"
          ''}";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # MinIO Client - S3互換CLI
            minio-client
            
            # 開発ツール
            jq
            curl
            gnumake
          ];

          shellHook = ''
            echo "Cloudflare R2 CLI環境"
            echo ""
            
            # .env.localファイルが存在する場合は自動的に読み込む
            if [ -f .env.local ]; then
              source .env.local
              echo "✓ 認証情報を.env.localから読み込みました"
              echo ""
              echo "利用可能なツール:"
              echo "  - mc: MinIO Client（S3互換CLI）"
              echo ""
              echo "使用例:"
              echo "  mc ls r2/                    # バケット一覧"
              echo "  mc mb r2/my-bucket           # バケット作成"
              echo "  mc cp file.txt r2/my-bucket  # ファイルアップロード"
            else
              echo "⚠️  .env.localファイルが見つかりません"
              echo ""
              echo "利用可能なツール:"
              echo "  - mc: MinIO Client（S3互換CLI）"
              echo ""
              echo "セットアップ手順:"
              echo "  1. .env.localファイルを作成して認証情報を設定"
              echo "  2. MinIO Clientのエイリアスを設定:"
              echo "     mc alias set r2 https://[account-id].r2.cloudflarestorage.com [key] [secret]"
            fi
            echo ""
            
            # .envファイルのテンプレート作成
            if [ ! -f .env.example ]; then
              cat > .env.example << 'EOF'
#!/usr/bin/env bash
# Cloudflare R2 認証情報のテンプレート
# このファイルを.env.localにコピーして使用してください

# Cloudflare API Token
export CLOUDFLARE_API_TOKEN="your-api-token"

# R2 S3互換API認証情報
export R2_ACCESS_KEY_ID="your-access-key-id"
export R2_SECRET_ACCESS_KEY="your-secret-access-key"

# R2エンドポイント
export R2_ENDPOINT="https://[account-id].r2.cloudflarestorage.com"

# アカウントID
export CLOUDFLARE_ACCOUNT_ID="your-account-id"

# MinIO Client用エイリアス設定
export MC_HOST_r2="https://[ACCESS_KEY]:[SECRET_KEY]@[account-id].r2.cloudflarestorage.com"
EOF
              echo "📝 .env.exampleを作成しました"
            fi
          '';
        };
      });
}