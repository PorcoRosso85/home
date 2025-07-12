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
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Wrangler（Cloudflare公式CLI） - nixpkgsから直接
            wrangler
            
            # MinIO Client
            minio-client
            
            # AWS CLI（S3互換接続用） - オプション
            # awscli2
            
            # 開発ツール
            jq
            curl
            gnumake
            
            # セキュリティ（認証情報管理） - 本番環境で推奨
            # pass
            # gnupg
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
              echo "  - wrangler: Cloudflare公式CLI（認証済み）"
              echo "  - mc: MinIO Client（認証済み）"
              echo ""
              echo "使用例:"
              echo "  wrangler r2 bucket list"
              echo "  mc ls r2/"
            else
              echo "⚠️  .env.localファイルが見つかりません"
              echo ""
              echo "利用可能なツール:"
              echo "  - wrangler: Cloudflare公式CLI"
              echo "  - mc: MinIO Client（S3互換CLI）"
              echo ""
              echo "セットアップ手順:"
              echo "  1. .env.localファイルを作成して認証情報を設定"
              echo "  2. または手動で環境変数を設定:"
              echo "     export CLOUDFLARE_API_TOKEN='your-token'"
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
export MC_HOST_r2="https://${R2_ACCESS_KEY_ID}:${R2_SECRET_ACCESS_KEY}@[account-id].r2.cloudflarestorage.com"
EOF
              echo "📝 .env.exampleを作成しました"
            fi
          '';
        };
      });
}