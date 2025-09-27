# R2 Data Plane Operations Examples

**⚠️ WARNING: These are educational examples only. Data Plane operations are NOT part of this flake's scope.**

This directory contains sample implementations of R2 Data Plane operations to demonstrate what this flake explicitly does NOT do.

## Data Plane vs Control Plane

### Control Plane (This Flake's Scope)
- **Purpose**: Resource management and configuration
- **Operations**: Deploy, configure, manage R2 buckets and workers
- **Examples**: Creating buckets, setting CORS policies, configuring bindings
- **Tools**: Pulumi, Wrangler, infrastructure as code

### Data Plane (NOT This Flake's Scope)
- **Purpose**: Actual data operations
- **Operations**: Store, retrieve, delete, list objects
- **Examples**: Uploading files, downloading content, managing object metadata
- **Tools**: Worker runtime, R2 API, application code

## Example Files

### 1. `put-object.ts`
Demonstrates uploading objects to R2 bucket with metadata.
- **Operation**: `PUT /{objectKey}`
- **Function**: Stores file content in R2
- **Features**: Content-Type handling, custom metadata

### 2. `get-object.ts`
Demonstrates retrieving objects from R2 bucket.
- **Operation**: `GET /{objectKey}`
- **Function**: Retrieves file content from R2
- **Features**: Range requests, caching headers, content streaming

### 3. `delete-object.ts`
Demonstrates removing objects from R2 bucket.
- **Operation**: `DELETE /{objectKey}`
- **Function**: Removes file from R2
- **Features**: Existence checking, error handling

### 4. `list-objects.ts`
Demonstrates listing objects in R2 bucket.
- **Operation**: `GET /?prefix=...&limit=...`
- **Function**: Lists bucket contents with filtering
- **Features**: Pagination, prefix filtering, metadata extraction

## Usage Instructions

**These examples are for educational purposes only and should NOT be deployed using this flake.**

To use these examples in your own projects:

1. **Copy the relevant example** to your own Cloudflare Worker project
2. **Modify the binding names** to match your R2 bucket configuration
3. **Add proper authentication** and authorization logic
4. **Implement error handling** appropriate for your use case
5. **Deploy using standard Wrangler** commands, not this flake

## Important Notes

### Why These Are Separate
- **Separation of Concerns**: Infrastructure (Control Plane) and application logic (Data Plane) have different lifecycles
- **Security**: Data operations require different security models than infrastructure management
- **Scalability**: Data operations need runtime optimization, infrastructure operations need deployment optimization
- **Maintainability**: Mixing Control and Data Plane operations creates complex, hard-to-maintain systems

### This Flake's Actual Purpose
This flake is designed to:
- Deploy and configure R2 buckets
- Set up worker bindings
- Manage CORS and security policies
- Handle secrets and environment configuration
- Provide infrastructure as code for Cloudflare resources

### What to Use Instead
For Data Plane operations, use:
- **Standard Cloudflare Workers** with proper R2 bindings
- **Application frameworks** like Hono, Itty Router, or custom logic
- **Direct R2 API** integration in your applications
- **CDK/SDK libraries** for programmatic access

## Related Documentation

- [Cloudflare R2 API Documentation](https://developers.cloudflare.com/r2/api/)
- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [R2 Bindings Documentation](https://developers.cloudflare.com/workers/wrangler/configuration/#r2-buckets)
- [This Flake's SCOPE.md](../SCOPE.md) for Control Plane details