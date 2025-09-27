# RedwoodSDK R2 Connection Management System

A comprehensive system for managing Cloudflare R2 storage connections with clear separation between local development (Miniflare) and production deployment scenarios.

## 🎯 Scope: Resource Plane Operations Only

**This flake focuses exclusively on Resource Plane (infrastructure) operations:**
- ✅ **Resource management**: R2 bucket configuration, Worker deployment, secret management
- ✅ **Configuration generation**: wrangler.jsonc, connection manifests, environment setup
- ✅ **Validation & testing**: Configuration validation, connection testing, security checks

**Data Plane operations are explicitly out of scope:**
- ❌ **R2 object operations**: PUT/GET/DELETE of actual data files
- ❌ **Business logic**: Application-specific data processing
- ❌ **End-user functionality**: HTTP APIs serving application data

> 📚 **See [SCOPE.md](./SCOPE.md) for detailed scope definition and architectural separation.**

Examples of Data Plane operations are provided in the `examples/` directory for educational purposes only.

## 🎯 Overview

This system provides Resource Plane management capabilities:
- **⚙️ Configuration Management**: Generate and validate wrangler.jsonc and connection manifests
- **🚀 Infrastructure Ready**: R2 bucket and Worker resource configuration
- **🔒 Security First**: SOPS-encrypted secrets with plaintext detection
- **🌍 Multi-Environment**: Support for dev, staging, and production environments
- **📋 Schema Validation**: TypeScript-first configuration with JSON Schema validation
- **📊 Resource Inventory**: View current Cloudflare resource status

## 🚀 Quick Start

### 📍 Choose Your Development Path

#### 🧪 **Configuration Development** (Recommended for getting started)
Perfect for developing and testing Resource Plane configurations without external dependencies.

```bash
# 1. Enter development environment
nix develop

# 2. Initialize basic configuration
just setup

# 3. Validate R2 configuration
just r2:test dev

# 4. View configuration status
just status
```

**✅ What this gives you:**
- Configuration generation and validation
- Schema validation and syntax checking
- Security validation (plaintext secret detection)
- Multi-environment configuration management

#### 🚀 **Production Resource Management** (When you're ready to deploy)
For managing real Cloudflare R2 buckets and Workers in production.

```bash
# 1. Set up encrypted secrets
just secrets-init

# 2. Configure your R2 connection details
cp r2.yaml.example secrets/r2.yaml
just secrets-edit secrets/r2.yaml

# 3. Generate production configuration
just r2:gen-config prod

# 4. View resource inventory
just res:inventory prod

# 5. Deploy to Cloudflare Workers
wrangler deploy
```

**✅ What this gives you:**
- Real R2 bucket and Worker resource management
- Production-ready configuration generation
- Encrypted secret management
- Resource inventory and status monitoring
- Multi-environment support

## 📋 SOT Integration Progress

🎉 **ALL PHASES COMPLETED** - SOT Integration Successfully Implemented (2025-09-28)

### 🎯 Core Requirements Implementation Status

#### ✅ Phase 1: Documentation & Message Consistency (COMPLETED)
- [x] Resource/Data Plane separation established
- [x] Documentation updated for Resource Plane focus
- [x] Command descriptions aligned with current behavior
- [x] Security guards implemented

#### ✅ Phase 2: Single Source of Truth (SOT) Introduction (COMPLETED)
- [x] `spec/{dev,stg,prod}/` directory structure created
- [x] SOPS configuration updated for spec/ files
- [x] JSON Schema defined for SOT validation
- [x] DevShell updated with Pulumi and AJV CLI
- [x] Existing generators converted to SOT-driven
- [x] SOT-driven configuration validation implemented

#### ✅ Phase 3: Drift Detection (COMPLETED)
- [x] Remote state fetching implemented (`just res:fetch-state`)
- [x] SOT comparison logic implemented (`just res:diff`)
- [x] Drift detection integrated into `nix flake check`
- [x] CI/CD pipeline integration

#### ✅ Phase 4: Pulumi IaC Automation (COMPLETED)
- [x] Pulumi project structure established
- [x] Environment-specific stacks created (dev/stg/prod)
- [x] SOT → Pulumi direct reading implemented
- [x] CLI commands: `just cf:plan/apply/destroy {env}`
- [x] Safety gates: diff=0 prerequisite for apply
- [x] R2 Control Plane example implementation

## 📚 Documentation

### Core Guides
- **[🧪 Local Development Guide](docs/local-development.md)** - Complete Miniflare setup and usage
- **[🚀 Production Setup Guide](docs/production-setup.md)** - Real R2 connection configuration
- **[🔧 AWS SDK v3 Integration](docs/aws-sdk-integration.md)** - Using AWS SDK with R2
- **[🔒 Security Guide](docs/security-guide.md)** - Best practices and security considerations

### Reference Documentation
- **[📋 Command Reference](docs/command-reference.md)** - All available commands and options
- **[🌍 Environment Management](docs/environment-management.md)** - Multi-environment configuration
- **[🔧 Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[📖 Migration Guide](docs/migration-guide.md)** - Upgrading from previous versions

## ⚡ Common Commands

### 🔧 Setup & Configuration
```bash
just help                    # Show all available commands
just setup                   # Complete R2 setup (secrets + config)
just status                  # Show configuration status
just clean                   # Clean generated files
```

### 🔐 Secret Management
```bash
just secrets:init            # Initialize encrypted secrets
just secrets:edit            # Edit R2 secrets securely
just secrets:check           # Validate secret security
```

### 🌍 Environment Management
```bash
just r2:envs                 # List available environments
just r2:status dev           # Show dev environment status
just r2:quick dev            # Quick setup for dev environment
just r2:deploy-prep prod     # Prepare production deployment
```

### 🧪 Testing & Validation
```bash
just r2:test dev             # Test locally with Miniflare
just r2:validate prod        # Validate production config
just r2:validate-all         # Validate all environments
```

## 🎛️ Configuration Overview

### 🧪 Local Development Configuration
- **Target**: Local testing and development
- **Authentication**: None required
- **R2 Simulation**: Miniflare handles all operations
- **Files**: Basic `wrangler.jsonc` with local settings
- **Commands**: `just r2:test dev`, `wrangler dev --local`

### 🚀 Production Configuration
- **Target**: Real Cloudflare R2 buckets
- **Authentication**: API tokens and R2 credentials required
- **Security**: SOPS-encrypted secrets
- **Files**: Environment-specific manifests and configurations
- **Commands**: `just r2:deploy-prep prod`, `wrangler deploy`

## 🔒 Security Features

- **📋 Plaintext Detection**: Automatic scanning for exposed credentials
- **🔐 SOPS Encryption**: Age-based encryption for all secrets
- **🛡️ Schema Validation**: TypeScript and JSON Schema validation
- **🔍 Security Auditing**: Built-in security checks and validation

## ⚠️ Important Usage Guidelines

### 🧪 For Local Development (Miniflare)
```bash
# ✅ DO: Use for development and testing
just r2:test dev
wrangler dev --local

# ❌ DON'T: Use for production deployment
# ❌ DON'T: Expect real R2 bucket persistence
```

### 🚀 For Production Deployment
```bash
# ✅ DO: Set up proper authentication
just secrets-edit

# ✅ DO: Validate before deploying
just r2:validate prod

# ❌ DON'T: Deploy without secret encryption
# ❌ DON'T: Use dev configuration in production
```

## 🆘 Need Help?

- **📖 Full Documentation**: Check the `/docs` directory for comprehensive guides
- **🔧 Troubleshooting**: See [docs/troubleshooting.md](docs/troubleshooting.md) for common issues
- **💡 Examples**: Browse `/examples` directory for usage patterns
- **🛠️ Commands**: Run `just help` for all available commands

## 🧩 Integration Points

This system integrates with:
- **Cloudflare Workers**: Direct R2 binding support
- **AWS SDK v3**: S3-compatible API integration
- **TypeScript**: Full type safety and validation
- **Nix**: Reproducible development environment

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

