# ===== DOCKERFILE RESPONSIBILITY & DEPENDENCIES =====
# 責務: Sliplane向けNixOS HTTPサーバーコンテナの構築・実行環境定義
# 機能: flake.nixベースの最小構成コンテナでポート8080のHTTPサーバー提供
# 依存: 
#   - flake.nix (Nixパッケージ・アプリケーション定義)
#   - flake.lock (依存バージョン固定)
#   - nixos/nix:latest (ベースイメージ)
# 相互関係:
#   - flake.nixで定義されたserverアプリを実行
#   - README.mdで記載されたSliplane設定に対応
#   - test.shによる動作確認対象
# ========================================================

# NixOS最小構成でflake.nixを使用
FROM nixos/nix:latest

# Nixの実験的機能を有効化（flakes使用のため）
RUN echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf

# 作業ディレクトリ
WORKDIR /app

# flake.nixとflake.lockをコピー（存在する場合）
COPY flake.nix flake.lock* ./

# flakeの依存関係を事前にダウンロード（キャッシュ効率化）
RUN nix flake metadata . && \
    nix flake show . && \
    nix build .#default --no-link

# HTTPサーバーアプリケーションを実行
# flake.nixで定義されたserverアプリを使用
RUN nix build .#server --no-link --print-out-paths > /tmp/server-path

# 実行スクリプトを作成（flakeを使用）
RUN echo '#!/bin/sh' > /app/run.sh && \
    echo 'echo "=== Starting NixOS container with flake.nix ===="' >> /app/run.sh && \
    echo 'echo "Using flake configuration from: $(pwd)"' >> /app/run.sh && \
    echo 'echo ""' >> /app/run.sh && \
    echo '# flakeで定義されたserverアプリを実行' >> /app/run.sh && \
    echo 'exec nix run .#server' >> /app/run.sh && \
    chmod +x /app/run.sh

# ポート公開（Sliplane用）
EXPOSE 8080

# ヘルスチェック用（ncがflakeから提供される）
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD nix run .#default -c sh -c "nc -z localhost 8080" || exit 1

# コンテナ起動時にflakeのserverアプリを実行
CMD ["/app/run.sh"]