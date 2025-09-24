# R2 Environment-Specific Secrets

This directory contains environment-specific encrypted secret files for Cloudflare R2 configuration.

## Structure

```
secrets/r2/
├── dev.yaml.template    # Development environment template
├── stg.yaml.template    # Staging environment template
├── prod.yaml.template   # Production environment template
├── dev.yaml            # Encrypted dev secrets (not in git)
├── stg.yaml            # Encrypted staging secrets (not in git)
└── prod.yaml           # Encrypted production secrets (not in git)
```

## Usage

### 1. Create Secret Files from Templates

```bash
# Copy templates to actual secret files
cp secrets/r2/dev.yaml.template secrets/r2/dev.yaml
cp secrets/r2/stg.yaml.template secrets/r2/stg.yaml
cp secrets/r2/prod.yaml.template secrets/r2/prod.yaml
```

### 2. Configure Secrets

Edit each file with your actual configuration values:

```bash
# Edit development secrets
nix run .#secrets-edit -- secrets/r2/dev.yaml

# Edit staging secrets
nix run .#secrets-edit -- secrets/r2/stg.yaml

# Edit production secrets
nix run .#secrets-edit -- secrets/r2/prod.yaml
```

### 3. Validate Configuration

Run validation to ensure all secrets are properly configured:

```bash
# Validate all environments
./scripts/validate-environment-secrets.sh

# Validate specific environment
./scripts/validate-environment-secrets.sh check-env dev
```

### 4. Load Secrets in Code

```typescript
import { loadR2ConfigForEnvironment } from '../src/environment-secrets';

// Load environment-specific configuration
const config = await loadR2ConfigForEnvironment('prod');
```

## Configuration Structure

Each environment file contains:

- **Environment metadata**: name, description, dates
- **Cloudflare settings**: account_id, buckets, endpoints
- **Security configuration**: authentication, rate limiting, etc.
- **Environment-specific settings**: CORS, monitoring, etc.

## Security Notes

- ✅ Actual secret files (`*.yaml`) are encrypted with SOPS and excluded from git
- ✅ Templates (`*.yaml.template`) are safe to commit and contain no secrets
- ✅ Different encryption keys can be used per environment if needed
- ⚠️ Always validate files before deployment: `./scripts/validate-environment-secrets.sh`

## Environment-Specific Features

### Development (`dev.yaml`)
- Relaxed security settings
- localhost CORS origins
- Debug mode enabled
- Short retention periods

### Staging (`stg.yaml`)
- Production-like security
- Test mode features
- Moderate retention
- QA-friendly settings

### Production (`prod.yaml`)
- Maximum security settings
- Monitoring and alerting
- Long retention periods
- Backup configurations