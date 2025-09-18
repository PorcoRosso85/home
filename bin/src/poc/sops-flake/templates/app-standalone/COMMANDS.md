# コマンドリファレンス - App-Standalone Template

## 初期化

| コマンド | 説明 |
|---------|------|
| `./scripts/init-template.sh` | テンプレート完全初期化（Age鍵生成、.sops.yaml設定、Git hooks） |
| `./scripts/setup-age-key.sh` | Age鍵生成/確認（既存鍵がある場合は公開鍵表示） |
| `./scripts/setup-ssh-recipient.sh` | SSH鍵をSOPS受信者として設定 |

## 開発

| コマンド | 説明 |
|---------|------|
| `nix develop` | 開発環境起動（sops、nixコマンド、開発ツール利用可能） |
| `nix flake check` | Flake検証（構文とビルド可能性チェック） |
| `nix build` | アプリケーションビルド実行 |
| `nix build .#container` | Dockerコンテナイメージビルド |
| `nix build .#packages.x86_64-linux.default` | デフォルトパッケージビルド（プラットフォーム指定） |

## シークレット管理

| コマンド | 説明 |
|---------|------|
| `sops edit secrets/app.yaml` | シークレット編集（暗号化されたファイルを復号化して編集） |
| `sops decrypt secrets/app.yaml` | 一時復号化（内容確認用） |
| `sops -e -i secrets/app.yaml` | 手動暗号化（平文ファイルを暗号化） |
| `./scripts/verify-encryption.sh` | 暗号化確認（secrets/内全ファイルの暗号化状態チェック） |
| `./scripts/check-no-plaintext-secrets.sh` | 平文シークレットチェック（Git commit前の検証） |
| `sops updatekeys secrets/app.yaml` | 暗号化鍵更新（新しい公開鍵を.sops.yamlに追加後） |

## SSH受信者管理
| コマンド | 説明 |
|---------|------|
| `./scripts/setup-ssh-recipient.sh` | SSH鍵をSOPS受信者として設定 |
| `ssh-to-age -i ~/.ssh/id_ed25519.pub` | SSH公開鍵をage形式に変換 |
| `ssh-to-age -i ~/.ssh/id_rsa.pub` | SSH鍵のRSA版変換 |

## 実行

| コマンド | 説明 |
|---------|------|
| `nix run` | アプリケーション直接実行 |
| `nix run . -- --help` | アプリケーション実行（ヘルプ表示） |
| `nix run . -- --port 8080` | アプリケーション実行（ポート指定） |
| `nix run . -- --config production` | アプリケーション実行（設定指定） |
| `nix run github:yourorg/my-app` | リモートからの直接実行 |

## コンテナ

| コマンド | 説明 |
|---------|------|
| `docker load < result` | ビルドしたコンテナイメージの読み込み |
| `docker run -p 8080:8080 my-app:latest` | コンテナ実行（ポートフォワード付き） |
| `docker run -e SOPS_AGE_KEY="$AGE_KEY" my-app:latest` | コンテナ実行（Age鍵環境変数指定） |
| `docker run -v /path/to/keys.txt:/keys.txt -e SOPS_AGE_KEY_FILE=/keys.txt my-app:latest` | コンテナ実行（Age鍵ファイルマウント） |

## デプロイ

| コマンド | 説明 |
|---------|------|
| `nix copy --to ssh://server .#packages.x86_64-linux.default` | SSHでのリモートデプロイ |
| `nix copy --to s3://bucket .#packages.x86_64-linux.default` | S3へのアーティファクト保存 |
| `docker push my-registry/my-app:latest` | コンテナレジストリへのプッシュ |

## 開発環境内での作業

| コマンド | 説明 |
|---------|------|
| `cargo run` | Rustプロジェクトの実行 |
| `cargo build` | Rustプロジェクトのビルド |
| `cargo test` | Rustプロジェクトのテスト |
| `npm start` | Node.jsプロジェクトの開始 |
| `npm run build` | Node.jsプロジェクトのビルド |
| `npm test` | Node.jsプロジェクトのテスト |
| `python main.py` | Pythonスクリプトの実行 |
| `python -m pytest` | Pythonテストの実行 |

## トラブルシューティング

| コマンド | 説明 |
|---------|------|
| `nix flake show` | Flakeの出力確認（利用可能なパッケージ・アプリ一覧） |
| `nix flake update` | 依存関係更新（flake.lock更新） |
| `nix show-derivation` | ビルド設定詳細表示 |
| `nix log .#packages.x86_64-linux.default` | ビルドログ確認 |
| `age-keygen -y ~/.config/sops/age/keys.txt` | Age公開鍵確認 |
| `echo $SOPS_AGE_KEY_FILE` | SOPS鍵ファイル設定確認 |
| `sops --version` | SOPSバージョン確認 |
| `docker version` | Dockerバージョン確認 |

## Git管理

| コマンド | 説明 |
|---------|------|
| `git add secrets/app.yaml .sops.yaml` | 暗号化ファイルと設定をステージング |
| `git status` | 平文ファイルが誤ってステージングされていないかチェック |
| `git commit -m "feat: add encrypted secrets"` | 暗号化ファイルのコミット |
| `git log --oneline secrets/` | シークレット変更履歴確認 |
| `git tag v1.0.0` | バージョンタグ作成 |

## テスト・検証

| コマンド | 説明 |
|---------|------|
| `nix eval .#packages.x86_64-linux.default` | パッケージ定義確認 |
| `nix eval .#apps.x86_64-linux.default` | アプリケーション定義確認 |
| `nix build --dry-run` | ビルド予定の確認（実際のビルドは行わない） |
| `curl -f http://localhost:8080/health` | アプリケーション稼働確認（ヘルスチェック） |

## 設定確認

| コマンド | 説明 |
|---------|------|
| `nix show-config` | Nix設定確認 |
| `docker inspect my-app:latest` | コンテナイメージ詳細確認 |
| `nix path-info .#packages.x86_64-linux.default` | パッケージパス情報 |

## パフォーマンス・分析

| コマンド | 説明 |
|---------|------|
| `nix build --print-build-logs` | ビルド時のログ出力 |
| `nix why-depends .#packages.x86_64-linux.default nixpkgs#glibc` | 依存関係解析 |
| `nix store diff-closures .#packages.x86_64-linux.default ./result-old` | パッケージサイズ差分確認 |
| `docker images my-app` | コンテナイメージサイズ確認 |

## CI/CD関連

| コマンド | 説明 |
|---------|------|
| `nix build --print-out-paths` | 出力パスの取得（CI/CD用） |
| `nix copy --to binary-cache .#packages.x86_64-linux.default` | バイナリキャッシュへの保存 |
| `nix build --fallback` | ネットワーク障害時のローカルビルド |

## 環境情報

| コマンド | 説明 |
|---------|------|
| `uname -a` | システム情報 |
| `nix --version` | Nixバージョン |
| `which sops age docker` | 必要ツールのパス確認 |
| `df -h /nix/store` | Nixストア容量確認 |