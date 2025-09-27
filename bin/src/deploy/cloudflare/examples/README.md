# Examples Directory

**⚠️ IMPORTANT: All examples in this directory are for educational purposes only and are NOT part of this flake's scope.**

This directory contains examples that demonstrate what this flake does NOT do, to help clarify the boundaries between Control Plane and Data Plane operations.

## Scope Clarification

### This Flake's Scope (Control Plane)
This flake is designed exclusively for **Control Plane operations**:
- ✅ **Resource Management**: Deploy and configure R2 buckets
- ✅ **Worker Deployment**: Deploy minimal workers for resource binding verification
- ✅ **Infrastructure as Code**: Manage Cloudflare resources via Pulumi
- ✅ **Configuration Management**: Handle secrets, environment variables, CORS policies
- ✅ **Binding Management**: Set up R2 bucket bindings for workers

### Outside This Flake's Scope (Data Plane)
This flake explicitly does NOT handle **Data Plane operations**:
- ❌ **Object Storage**: PUT/GET/DELETE operations on R2 objects
- ❌ **Content Management**: File uploads, downloads, streaming
- ❌ **Data Processing**: Image resizing, format conversion, etc.
- ❌ **Application Logic**: Business logic that operates on stored data
- ❌ **User-Facing APIs**: Public endpoints for data access

## Directory Structure

```
examples/
├── README.md                           # This file
├── r2-data-operations/                 # Data Plane examples (NOT flake scope)
│   ├── README.md                       # Data Plane operation explanations
│   ├── put-object.ts                   # Example: Upload objects to R2
│   ├── get-object.ts                   # Example: Download objects from R2
│   ├── delete-object.ts                # Example: Delete objects from R2
│   └── list-objects.ts                 # Example: List bucket contents
├── environment-secrets-usage.ts        # Environment variable access patterns
├── r2.dev.json.example                 # Development environment config
└── r2.prod.json.example                # Production environment config
```

## Why Examples Are Separate

### 1. **Separation of Concerns**
- **Infrastructure** (this flake) has different requirements than **application logic**
- **Deployment lifecycle** differs from **runtime lifecycle**
- **Security models** are different for infrastructure vs data operations

### 2. **Clarity of Purpose**
- This flake focuses on getting R2 resources ready for use
- Applications focus on using those resources for business logic
- Clear boundaries prevent feature creep and maintenance complexity

### 3. **Reusability**
- Infrastructure setup can be reused across multiple applications
- Applications can choose their own data operation patterns
- Teams can specialize in infrastructure OR application development

## How to Use These Examples

### ❌ Don't Do This
```bash
# This won't work - examples are not deployable via this flake
nix run . -- deploy --include-examples
```

### ✅ Do This Instead
1. **Use this flake** to set up your R2 infrastructure:
   ```bash
   nix run . -- deploy --environment dev
   ```

2. **Copy relevant examples** to your own application project:
   ```bash
   cp examples/r2-data-operations/put-object.ts ../my-app/src/
   ```

3. **Deploy your application** using standard tools:
   ```bash
   cd ../my-app
   npx wrangler deploy
   ```

## Example Use Cases

### Control Plane (This Flake)
```yaml
# What this flake manages
resources:
  - R2 bucket creation with proper naming
  - CORS policy configuration
  - Worker deployment with R2 bindings
  - Secret management for API keys
  - Environment-specific configurations
```

### Data Plane (Your Application)
```typescript
// What your application handles
export default {
  async fetch(request: Request, env: Env) {
    if (request.method === 'POST') {
      return handleFileUpload(request, env.USER_UPLOADS);
    }
    if (request.method === 'GET') {
      return handleFileDownload(request, env.USER_UPLOADS);
    }
    // ... your business logic here
  }
};
```

## Related Documentation

- **[SCOPE.md](../SCOPE.md)**: Detailed scope definition for this flake
- **[README.md](../README.md)**: Main flake documentation and usage
- **[r2-data-operations/README.md](r2-data-operations/README.md)**: Detailed Data Plane examples

## Key Takeaway

**This flake gets your R2 infrastructure ready. Your application uses that infrastructure.**

The examples show you what your application might do, but they are not part of this flake's deployment process.