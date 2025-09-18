# CI/CD Setup Guide

## GitHub Actions

The base environment includes GitHub Actions workflow for automated deployment.

### Setup Steps

1. **Copy the workflow to your project**:
   ```bash
   cp -r .github your-waku-app/
   ```

2. **Set up Cloudflare API Token**:
   - Go to Cloudflare Dashboard → My Profile → API Tokens
   - Create token with "Edit Cloudflare Workers" permission
   - Add as `CLOUDFLARE_API_TOKEN` in GitHub repository secrets

3. **Workflow triggers**:
   - Push to main: Build and deploy
   - Pull requests: Build only (no deployment)

## Other CI Platforms

### GitLab CI
```yaml
# .gitlab-ci.yml
stages:
  - build
  - deploy

before_script:
  - curl -L https://nixos.org/nix/install | sh
  - . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh

build:
  stage: build
  script:
    - nix run .#build

deploy:
  stage: deploy
  script:
    - nix run .#deploy
  only:
    - main
```

### CircleCI
```yaml
# .circleci/config.yml
version: 2.1
orbs:
  nix: eld/nix@1.0.0

jobs:
  build-and-deploy:
    executor: nix/default
    steps:
      - checkout
      - run: nix run .#build
      - run:
          name: Deploy
          command: nix run .#deploy
```

## Environment Variables

Required for deployment:
- `CLOUDFLARE_API_TOKEN`: Your CF API token
- `CLOUDFLARE_ACCOUNT_ID`: Your CF account ID (can be set in wrangler.toml)

## Local Testing

```bash
# Test build locally
nix run .#build

# Test deployment (dry-run)
nix shell . -c wrangler deploy --dry-run
```