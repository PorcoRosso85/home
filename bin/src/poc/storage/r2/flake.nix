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
        
        # Node.js環境（Wrangler用）
        nodejs = pkgs.nodejs_20;
        
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Wrangler（Cloudflare公式CLI）
            nodejs
            nodePackages.npm
            
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
            echo "利用可能なツール:"
            echo "  - wrangler: Cloudflare公式CLI（npm install -g wranglerで初回インストール）"
            echo "  - mc: MinIO Client（S3互換CLI）"
            # echo "  - aws: AWS CLI（S3互換接続） - オプション"
            echo ""
            echo "セットアップ手順:"
            echo "  1. npm install -g wrangler"
            echo "  2. wrangler login または export CLOUDFLARE_API_TOKEN='your-token'"
            echo "  3. mc alias set r2 https://[account-id].r2.cloudflarestorage.com [key] [secret]"
            echo ""
            
            # package.jsonがない場合は作成
            if [ ! -f package.json ]; then
              echo '{"private": true}' > package.json
            fi
            
            # .envファイルのテンプレート作成
            if [ ! -f .env.example ]; then
              cat > .env.example << 'EOF'
# Cloudflare R2設定
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_API_TOKEN=your-api-token

# R2 S3互換API認証情報
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-access-key
R2_ENDPOINT=https://[account-id].r2.cloudflarestorage.com
EOF
              echo ".env.exampleを作成しました"
            fi
          '';
        };
      });
}