# Cloudflare Deployment - Pulumi Infrastructure

This directory contains Pulumi infrastructure-as-code for managing Cloudflare resources.

## Setup

1. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your Cloudflare credentials
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Select Stack**
   ```bash
   # For development
   pulumi stack select dev

   # For staging
   pulumi stack select stg

   # For production
   pulumi stack select prod
   ```

## Safety Features

- **Preview-Only Mode**: All stacks are configured with `previewOnly: true` by default
- **No Auto-Apply**: Deployments require explicit confirmation
- **Environment Isolation**: Separate stacks for dev/stg/prod

## Commands

- `npm run preview` - Preview changes
- `npm run up` - Deploy (preview-only by default)
- `npm run destroy` - Destroy resources (preview-only by default)

## Security

- Environment variables are encrypted in stack configurations
- API tokens should have minimal required permissions:
  - Zone:Edit (for zone management)
  - Account:Read (for account access)

## Note

This configuration is designed for safety and requires manual confirmation for all operations. To enable actual deployments, modify the `previewOnly` settings in the stack configurations.