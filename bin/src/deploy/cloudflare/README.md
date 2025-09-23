# RedwoodSDK R2 Connection Info Local Completion System

## Usage

### Quick Start (Local Development)

```bash
# 1. Enter development environment
nix develop

# 2. Initialize encrypted secrets
just secrets-init

# 3. Configure R2 connection (edit with your account details)
cp r2.yaml.example secrets/r2.yaml
just secrets-edit

# 4. Test R2 connection locally (uses Miniflare - no authentication required)
just r2:test

# 5. Check security (no plaintext secrets)
just r2:check-secrets
```

### Available Commands

- `just r2:status` - Check configuration status
- `just r2:gen-config` - Generate wrangler.jsonc with R2 configuration
- `just r2:test` - Test R2 operations locally via Miniflare
- `just r2:check-secrets` - Validate secret security
- `just secrets-init` - Initialize Age encryption
- `just secrets-edit` - Edit encrypted R2 secrets

### Local-Only Testing

This system uses **local-only** testing via Miniflare (`wrangler dev --local`):
- ✅ No external API calls or authentication required
- ✅ R2 operations simulated locally (PUT/GET/HEAD/DELETE)
- ✅ Side-effect-free development and testing
- ⚠️  For production use, configure `CLOUDFLARE_API_TOKEN` and use `wrangler dev --remote`

---

## Infrastructure Philosophy

  - Pulumi状態: ローカル/自前バックエンドで管理（.pulumi or 自前S3/R2
  等）。チーム共有なしならローカルFSで完結。
  - R2統合: Cloudflare R2をローカル開発で使用。接続情報はSOPS暗号化で管理。
  - Secrets: Pulumiのlocal secretsでローカル暗号化（PGP/age）。クラ
  ウドKMSは不使用。
  - 再現性: Nix/固定バージョン/コンテナdigest固定。latestや外部apt
  更新は禁止。flake.lock必須。
  - 資格情報: プロバイダAPI鍵・各種トークンはPulumi secretsで一元管
  理（平文配置なし）。
  - 事前生成アセット: WG/SSH/アプリ用鍵束、クラスタjoin token（必要
  なら）を事前生成し暗号化保管。
  - ネットワーク計画: 固定プライベートCIDRと各ノード固定IPを採用。
  Public IPを使う場合も静的割当のみ。
  - サービス発見: 静的/etc/hosts、内部DNS（固定ゾーン）または静的
  Gossipシード（Consul/Serf）。外部DNS依存なし。
  - ブートストラップ: cloud-init/NixOS初期化は冪等・自己完結。初回
  で完結し再起動でも破綻しない。
  - トポロジ固定: ノード名/IP/ポートの固定リストを全ノードに同梱
  （テンプレ生成で配布）。
  - メッシュ接続: WireGuard等の事前生成鍵＋固定エンドポイントで自動
  接続（起動直後に到達可能）。
  - 動的値の排除: プロバイダ割当（IP/Volume ID等）やapplyの出力に依
  存せず、他ノードへ伝播も不要に設計。
  - スケール戦略: 台数固定。オートスケールや台数可変設計は採用し
  ない。
  - ログ/監視: ローカル完結（例: node-exporter/Prometheus/Grafana同
  梱）。外部SaaSを排除。
  - 変更運用: 鍵/トークンのローテは計画的な再デプロイで実施（完全静
  的の制約を受容）。
  - 供給元固定: イメージ/レジストリ/パッケージの出所とバージョンを
  固定。ビルド時のネット依存を最小化（可能ならキャッシュ/ミラー）。
  - ドキュメント化: 固定リスト・テンプレ・手順をリポジトリで管理
  し、生成物は再現可能に。

  Cloudflareを使う場合の追加要件

  - “外部更新なし”を厳密に守るならCloudflare非依存（/etc/hostsまた
  は内部DNSのみ）。
  - Cloudflare併用でも手元完結を維持するには:
      - ゾーン/レコードを事前に静的作成（固定A/AAAA/CNAMEが固定IPと
  一致）。
      - 運用中はDNS更新を行わない（初回のみ許容するなら、その更新も
  Pulumiから一度限り）。
      - APIトークンはPulumi secretsで保持。レコードTTL/プロキシ設定
  （オレンジ/グレー）も固定方針で不変。
  - 動的Public IPは不可。必要なら事前に静的IPを確保するか、内部メッ
  シュのみで到達させる。
  - Tailscaleは外部制御平面に依存するため“完全手元完結”と相反。
  WireGuard採用を推奨。

  実現パターン（いずれもPulumi→VPSで完結）

  - ゴールデンイメージ: Packer/Nixで完成品を事前作成。Pulumiは配備
  とNWのみ。
  - NixOS直適用: PulumiでVPS＋鍵配備→cloud-initでnixos-rebuild
  switch --flake。
  - メッシュ先行: 事前鍵＋固定IPを配布→起動即メッシュ→固定エンドポ
  イント通信。

