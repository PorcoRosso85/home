# RedwoodSDK 本番品質ボイラープレート完成仕様書

## 1. エグゼクティブサマリー

### 目的
RedwoodSDK-initを以下の2つの観点で完成させる：
1. **本番運用可能**: セキュリティ、監視、ロールバック対応
2. **横展開テンプレート**: 他プロジェクトで即座に再利用可能

### 現状と目標

| 観点 | 現状 | 目標 |
|------|------|------|
| テスト | 0件 ❌ | サンプル4件+基盤 ✅ |
| CI/CD | なし ❌ | 完全自動化 ✅ |
| セキュリティ | 基本のみ ⚠️ | 本番レベル ✅ |
| 横展開性 | 手動 ⚠️ | 自動化スクリプト ✅ |
| ドキュメント | 最小限 ⚠️ | 完全ガイド ✅ |

## 2. 完成形ディレクトリ構造

### 2.1 CI/CD基盤（/.github/workflows/）

```
/home/nixos/.github/workflows/
├── redwoodsdk-template.yml          # メインテンプレート
└── shared/                          # 再利用可能アクション
    ├── cloudflare-deploy.yml        # CF Workers デプロイ
    ├── nix-setup.yml               # Nix環境構築
    └── security-scan.yml           # セキュリティ検証
```

#### redwoodsdk-template.yml
```yaml
# RedwoodSDK アプリケーション用CI/CDテンプレート
name: RedwoodSDK CI/CD Template
on:
  workflow_call:
    inputs:
      project-path:
        required: true
        type: string
      environment:
        required: false
        type: string
        default: staging

jobs:
  validation:
    uses: ./.github/workflows/shared/nix-setup.yml
    with:
      working-directory: ${{ inputs.project-path }}
    
  security:
    uses: ./.github/workflows/shared/security-scan.yml
    needs: validation
    
  test:
    runs-on: ubuntu-latest
    needs: validation
    defaults:
      run:
        working-directory: ${{ inputs.project-path }}
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/nix-setup
      - run: |
          npm ci
          npm run test
          npm run test:e2e
    
  deploy:
    if: github.ref == 'refs/heads/main'
    needs: [test, security]
    uses: ./.github/workflows/shared/cloudflare-deploy.yml
    with:
      project-path: ${{ inputs.project-path }}
      environment: ${{ inputs.environment }}
    secrets: inherit
```

### 2.2 ボイラープレート本体強化

```
/home/nixos/bin/src/poc/redwoodsdk-init/
├── src/                             # 既存（アプリケーションコード）
├── tests/                           # 新規：テスト基盤
│   ├── setup/
│   │   ├── miniflare.ts            # Miniflare設定
│   │   ├── test-helpers.ts         # テストヘルパー
│   │   └── mock-factories.ts       # モックファクトリー
│   ├── unit/
│   │   ├── auth.test.ts            # WebAuthn単体テスト
│   │   └── session.test.ts         # セッション管理テスト
│   ├── integration/
│   │   ├── api.test.ts             # API統合テスト
│   │   └── db.test.ts              # DB操作テスト
│   ├── e2e/
│   │   └── user-flow.test.ts       # E2Eテスト例
│   └── README.md                    # テストガイド
├── templates/                       # 新規：設定テンプレート
│   ├── .env.template                # 環境変数テンプレート
│   ├── wrangler.template.jsonc     # Wrangler設定テンプレート
│   └── secrets.template.yml        # GitHub Secrets設定ガイド
├── scripts/                         # 新規：自動化スクリプト
│   ├── init-project.sh             # プロジェクト初期化
│   ├── setup-secrets.sh            # シークレット設定
│   ├── deploy-check.sh             # デプロイ前チェック
│   └── rollback.sh                 # ロールバックスクリプト
├── docs/                            # 新規：運用ドキュメント
│   ├── PRODUCTION_DEPLOY.md        # 本番デプロイ手順
│   ├── TEMPLATE_USAGE.md           # テンプレート使用方法
│   ├── SECURITY_GUIDE.md           # セキュリティガイド
│   ├── MONITORING.md               # 監視設定ガイド
│   └── TROUBLESHOOTING.md          # トラブルシューティング
├── vitest.config.ts                 # 新規：テスト設定
├── .env.example                     # 新規：環境変数例
├── BOILERPLATE.md                   # 新規：横展開専用ガイド
├── package.json                     # 更新：スクリプト追加
├── wrangler.jsonc                   # 更新：環境分離対応
└── README.md                        # 更新：完全ガイド
```

## 3. 詳細設計

### 3.1 テスト基盤

#### vitest.config.ts
```typescript
import { defineConfig } from 'vitest/config';
import { getCloudflareProxy } from 'wrangler';

export default defineConfig({
  test: {
    globals: true,
    environment: 'miniflare',
    setupFiles: ['./tests/setup/miniflare.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules', 'tests'],
      thresholds: {
        branches: 60,
        functions: 60,
        lines: 60,
        statements: 60
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src',
      '@test': '/tests'
    }
  }
});
```

#### tests/setup/test-helpers.ts
```typescript
// テストヘルパー関数
export function createMockRequest(options: RequestInit = {}): Request {
  return new Request('http://localhost', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });
}

export function createMockContext(): ExecutionContext {
  return {
    waitUntil: vi.fn(),
    passThroughOnException: vi.fn()
  };
}

export async function setupTestDatabase() {
  // テスト用DB初期化
  const db = await getD1Database('test');
  await db.exec('DELETE FROM User');
  await db.exec('DELETE FROM Credential');
  return db;
}
```

### 3.2 環境設定テンプレート

#### templates/.env.template
```bash
# Application Settings
NODE_ENV=development
APP_NAME={{PROJECT_NAME}}

# Cloudflare Settings
CLOUDFLARE_ACCOUNT_ID={{CF_ACCOUNT_ID}}
CLOUDFLARE_API_TOKEN={{CF_API_TOKEN}}

# Database
DATABASE_NAME={{PROJECT_NAME}}-{{ENVIRONMENT}}-db
DATABASE_ID={{DATABASE_ID}}

# WebAuthn
WEBAUTHN_RP_ID={{DOMAIN}}
WEBAUTHN_APP_NAME={{PROJECT_NAME}}
WEBAUTHN_ORIGIN=https://{{DOMAIN}}

# Security
SESSION_SECRET={{GENERATE_SECRET}}
ENCRYPTION_KEY={{GENERATE_KEY}}

# Monitoring (Optional)
SENTRY_DSN={{SENTRY_DSN}}
DATADOG_API_KEY={{DD_API_KEY}}

# Feature Flags
ENABLE_DEBUG_LOGGING=false
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60
```

### 3.3 自動化スクリプト

#### scripts/init-project.sh
```bash
#!/usr/bin/env bash
set -euo pipefail

# プロジェクト初期化スクリプト
# 使用法: ./scripts/init-project.sh <project-name> <environment>

PROJECT_NAME="${1:-}"
ENVIRONMENT="${2:-development}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# 引数チェック
if [[ -z "$PROJECT_NAME" ]]; then
    log_error "Usage: $0 <project-name> [environment]"
fi

log_info "Initializing project: $PROJECT_NAME ($ENVIRONMENT)"

# 1. 環境変数ファイル作成
log_info "Creating environment file..."
cp "$PROJECT_ROOT/templates/.env.template" "$PROJECT_ROOT/.env.$ENVIRONMENT"
sed -i "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$PROJECT_ROOT/.env.$ENVIRONMENT"
sed -i "s/{{ENVIRONMENT}}/$ENVIRONMENT/g" "$PROJECT_ROOT/.env.$ENVIRONMENT"

# 2. シークレット生成
log_info "Generating secrets..."
SESSION_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
sed -i "s/{{GENERATE_SECRET}}/$SESSION_SECRET/g" "$PROJECT_ROOT/.env.$ENVIRONMENT"
sed -i "s/{{GENERATE_KEY}}/$ENCRYPTION_KEY/g" "$PROJECT_ROOT/.env.$ENVIRONMENT"

# 3. Wrangler設定
log_info "Configuring wrangler..."
cp "$PROJECT_ROOT/templates/wrangler.template.jsonc" "$PROJECT_ROOT/wrangler.jsonc"
sed -i "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$PROJECT_ROOT/wrangler.jsonc"
sed -i "s/{{ENVIRONMENT}}/$ENVIRONMENT/g" "$PROJECT_ROOT/wrangler.jsonc"

# 4. D1データベース作成
log_info "Creating D1 database..."
DB_NAME="$PROJECT_NAME-$ENVIRONMENT-db"
if wrangler d1 create "$DB_NAME" 2>/dev/null; then
    DB_ID=$(wrangler d1 list | grep "$DB_NAME" | awk '{print $2}')
    sed -i "s/{{DATABASE_ID}}/$DB_ID/g" "$PROJECT_ROOT/.env.$ENVIRONMENT"
    sed -i "s/{{DATABASE_ID}}/$DB_ID/g" "$PROJECT_ROOT/wrangler.jsonc"
    log_info "Database created: $DB_ID"
else
    log_warn "Database may already exist or creation failed"
fi

# 5. 依存関係インストール
log_info "Installing dependencies..."
npm ci

# 6. マイグレーション実行
log_info "Running migrations..."
npm run migrate:$ENVIRONMENT

# 7. 初期テスト実行
log_info "Running initial tests..."
npm test

log_info "✅ Project initialization complete!"
log_info "Next steps:"
echo "  1. Update .env.$ENVIRONMENT with your specific values"
echo "  2. Configure GitHub Secrets (see templates/secrets.template.yml)"
echo "  3. Run: npm run dev"
```

#### scripts/deploy-check.sh
```bash
#!/usr/bin/env bash
set -euo pipefail

# デプロイ前チェックスクリプト

ENVIRONMENT="${1:-staging}"
CHECKS_PASSED=true

echo "🔍 Running pre-deployment checks for $ENVIRONMENT..."

# 1. 環境変数チェック
check_env() {
    local var=$1
    if [[ -z "${!var:-}" ]]; then
        echo "❌ Missing required env var: $var"
        CHECKS_PASSED=false
    else
        echo "✅ $var is set"
    fi
}

echo -e "\n📋 Environment Variables:"
check_env "CLOUDFLARE_API_TOKEN"
check_env "DATABASE_ID"
check_env "WEBAUTHN_RP_ID"

# 2. テスト実行
echo -e "\n🧪 Running tests:"
if npm test --silent; then
    echo "✅ All tests passed"
else
    echo "❌ Tests failed"
    CHECKS_PASSED=false
fi

# 3. ビルドチェック
echo -e "\n🔨 Build check:"
if npm run build; then
    echo "✅ Build successful"
else
    echo "❌ Build failed"
    CHECKS_PASSED=false
fi

# 4. セキュリティスキャン
echo -e "\n🔒 Security scan:"
if npm audit --production; then
    echo "✅ No vulnerabilities found"
else
    echo "⚠️  Vulnerabilities detected (review before deploy)"
fi

# 5. Wrangler設定検証
echo -e "\n⚙️  Wrangler configuration:"
if wrangler deploy --dry-run --env $ENVIRONMENT > /dev/null 2>&1; then
    echo "✅ Wrangler config valid"
else
    echo "❌ Wrangler config invalid"
    CHECKS_PASSED=false
fi

# 結果
echo -e "\n========================"
if $CHECKS_PASSED; then
    echo "✅ All checks passed! Ready to deploy."
    exit 0
else
    echo "❌ Some checks failed. Please fix before deploying."
    exit 1
fi
```

### 3.4 運用ドキュメント

#### docs/PRODUCTION_DEPLOY.md
```markdown
# 本番デプロイ手順書

## 前提条件
- [ ] Cloudflare アカウント作成済み
- [ ] GitHub リポジトリ設定済み
- [ ] ローカル開発環境構築済み

## デプロイフロー

### 1. 初回セットアップ
```bash
# プロジェクト初期化
./scripts/init-project.sh my-app production

# 環境変数確認・修正
vim .env.production

# シークレット設定
./scripts/setup-secrets.sh production
```

### 2. デプロイ前チェック
```bash
# 自動チェック実行
./scripts/deploy-check.sh production

# 手動確認項目
- [ ] 環境変数が本番用に設定されている
- [ ] データベースバックアップ取得済み
- [ ] ロールバック手順確認済み
```

### 3. デプロイ実行

#### Blue-Green デプロイ（推奨）
```bash
# Green環境にデプロイ
npm run deploy:green

# 動作確認
curl https://green.example.com/health

# トラフィック切り替え
npm run switch:production

# 監視（5分間）
npm run monitor:production
```

#### 直接デプロイ（開発環境のみ）
```bash
npm run deploy:staging
```

### 4. デプロイ後確認
- [ ] ヘルスチェックエンドポイント確認
- [ ] 主要機能の動作確認
- [ ] ログ監視開始
- [ ] メトリクス確認

### 5. ロールバック手順
```bash
# 自動ロールバック
./scripts/rollback.sh production

# 手動ロールバック
wrangler rollback --env production
```

## トラブルシューティング
詳細は [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) 参照
```

#### docs/BOILERPLATE.md
```markdown
# RedwoodSDK ボイラープレート横展開ガイド

## クイックスタート

### 1. プロジェクトコピー
```bash
# このボイラープレートをコピー
cp -r /path/to/redwoodsdk-init /path/to/new-project
cd /path/to/new-project

# Git初期化
rm -rf .git
git init
```

### 2. カスタマイズ
```bash
# プロジェクト初期化
./scripts/init-project.sh your-app-name development

# パッケージ名変更
npm pkg set name="@your-org/your-app"
```

### 3. CI/CD設定
```bash
# GitHub Actionsワークフロー作成
mkdir -p .github/workflows
cat > .github/workflows/ci.yml << 'EOF'
name: CI/CD
on:
  push:
    paths:
      - 'your-project-path/**'

jobs:
  ci:
    uses: /home/nixos/.github/workflows/redwoodsdk-template.yml
    with:
      project-path: your-project-path
    secrets: inherit
EOF
```

## カスタマイズポイント

### 必須変更箇所
1. `package.json` - name, version, description
2. `wrangler.jsonc` - name, route
3. `.env.*` - 環境固有の値

### オプション変更箇所
1. `src/` - ビジネスロジック
2. `tests/` - テストケース追加
3. `docs/` - プロジェクト固有ドキュメント

## ベストプラクティス
- テストを削除せず、追加する
- CI/CDパイプラインは維持する
- セキュリティ設定は強化のみ（弱体化禁止）
```

### 3.5 パッケージ設定更新

#### package.json（更新箇所）
```json
{
  "scripts": {
    // 既存スクリプト...
    
    // テスト関連
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:coverage": "vitest --coverage",
    "test:e2e": "vitest run --config vitest.e2e.config.ts",
    
    // デプロイ関連
    "deploy:staging": "wrangler deploy --env staging",
    "deploy:production": "./scripts/deploy-check.sh production && wrangler deploy --env production",
    "deploy:green": "wrangler deploy --env green",
    "switch:production": "wrangler dispatch-namespace update --namespace production --route green",
    
    // 運用関連
    "rollback": "./scripts/rollback.sh",
    "monitor": "wrangler tail --env production",
    "health": "curl -f https://api.example.com/health || exit 1",
    
    // 初期化
    "init": "./scripts/init-project.sh",
    "setup": "npm ci && npm run migrate:dev"
  },
  
  "devDependencies": {
    // 既存の依存関係...
    
    // テスト関連
    "vitest": "^1.0.0",
    "@vitest/ui": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0",
    "miniflare": "^3.0.0",
    "@cloudflare/vitest-pool-workers": "^0.1.0",
    
    // 品質関連
    "eslint": "^8.0.0",
    "prettier": "^3.0.0",
    "husky": "^9.0.0",
    "lint-staged": "^15.0.0"
  }
}
```

## 4. 実装計画

### Phase 1: 基盤構築（1日）
- [ ] テスト基盤セットアップ
- [ ] 基本的なテストケース作成
- [ ] vitest設定

### Phase 2: 自動化（1日）
- [ ] 初期化スクリプト作成
- [ ] デプロイチェックスクリプト
- [ ] ロールバックスクリプト

### Phase 3: CI/CD（0.5日）
- [ ] GitHub Actionsテンプレート作成
- [ ] 再利用可能ワークフロー定義
- [ ] セキュリティスキャン統合

### Phase 4: ドキュメント（0.5日）
- [ ] 運用ドキュメント作成
- [ ] 横展開ガイド作成
- [ ] トラブルシューティングガイド

### 合計工数: 3日

## 5. 品質基準

### 必須達成項目
- ✅ `npm test` で最低4つのテストが実行される
- ✅ `./scripts/init-project.sh` で新規プロジェクトが5分以内に起動
- ✅ CI/CDパイプラインが自動実行される
- ✅ 本番デプロイ手順が文書化されている
- ✅ ロールバック手順が自動化されている

### 品質メトリクス
- テストカバレッジ: 60%以上
- ビルド時間: 3分以内
- デプロイ時間: 5分以内
- 初期化時間: 5分以内

## 6. セキュリティ考慮

### 実装済みセキュリティ機能
- WebAuthn による強固な認証
- セッション管理（DurableObjects）
- HTTPS強制
- CSRFトークン

### 追加セキュリティ機能
- レート制限実装
- セキュリティヘッダー設定
- 依存関係の定期スキャン
- シークレットのローテーション機能

## 7. 監視・運用

### 監視項目
- アプリケーションヘルス
- エラーレート
- レスポンスタイム
- リソース使用率

### アラート設定
```yaml
alerts:
  - name: high-error-rate
    condition: error_rate > 1%
    action: notify-slack
    
  - name: slow-response
    condition: p95_latency > 1000ms
    action: notify-pagerduty
    
  - name: deployment-failure
    condition: deployment_status == failed
    action: auto-rollback
```

## 8. まとめ

### 成果物の価値
1. **即座に本番投入可能**: 全ての品質基準を満たす
2. **横展開が容易**: 5分で新規プロジェクト起動
3. **運用負荷最小**: 自動化により手動作業を削減
4. **教育的価値**: ベストプラクティスの実例

### 次のステップ
1. Developer による実装
2. テスト実行と検証
3. ドキュメントレビュー
4. 本番環境でのパイロット運用

---
*Created by Designer Y - 2025-09-07*
*Version: 1.0.0 - Production-Ready Boilerplate*