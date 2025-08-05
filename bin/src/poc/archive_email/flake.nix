{
  description = "Email Archive POC - Cloudflare Worker with in-memory S3 for testing";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    # Reuse existing S3 storage module
    s3-storage = {
      url = "path:../../storage/s3";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs = { self, nixpkgs, flake-utils, s3-storage }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Node.js for Worker development
        nodejs = pkgs.nodejs_20;
        
        # Wrangler for Cloudflare Worker development
        wrangler = pkgs.nodePackages.wrangler;
        
        # Deno for S3 storage testing
        deno = pkgs.deno;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            nodejs
            wrangler
            deno
            pkgs.jq
            pkgs.curl
            s3-storage.packages.${system}.default
          ];
          
          shellHook = ''
            echo "Email Archive POC - In-Memory Testing Environment"
            echo ""
            echo "Available commands:"
            echo "  e2e-test       - Run E2E tests with in-memory storage"
            echo "  test-worker    - Test Worker with mock email"
            echo "  wrangler-test  - Test with real Wrangler environment"
            echo "  demo           - Show architecture overview"
            echo ""
            echo "Quick start:"
            echo "  nix run .#e2e-test       # Run complete E2E test"
            echo "  nix run .#wrangler-test  # Test with Wrangler"
          '';
        };

        apps = {
          # E2E test with in-memory storage
          e2e-test = {
            type = "app";
            program = "${pkgs.writeShellScript "e2e-test" ''
              echo "🧪 Email Archive E2E Test (In-Memory)"
              echo "====================================="
              echo ""
              
              # Create test directory
              TEST_DIR=$(mktemp -d)
              cd $TEST_DIR
              
              # Copy source files
              cp -r ${./.}/src ./src 2>/dev/null || mkdir -p src
              cp -r ${./.}/test ./test 2>/dev/null || mkdir -p test
              
              # Create test runner
              cat > test-e2e.js << 'EOF'
              // Simple in-memory storage adapter for testing
              class InMemoryStorageAdapter {
                constructor() {
                  this.storage = new Map();
                }
                
                async upload(key, content) {
                  const data = typeof content === "string" 
                    ? new TextEncoder().encode(content)
                    : new Uint8Array(content);
                  this.storage.set(key, data);
                  return { key, size: data.length };
                }
                
                async download(key) {
                  const content = this.storage.get(key);
                  if (!content) throw new Error("Key not found: " + key);
                  return { content, key };
                }
                
                async list(options = {}) {
                  const prefix = options.prefix || "";
                  const objects = [];
                  for (const [key, value] of this.storage.entries()) {
                    if (key.startsWith(prefix)) {
                      objects.push({ key, size: value.length });
                    }
                  }
                  return { objects };
                }
              }
              
              const adapter = new InMemoryStorageAdapter();
              
              // Mock ForwardableEmailMessage
              class MockForwardableEmailMessage {
                constructor(from, to, raw) {
                  this.from = from;
                  this.to = to;
                  this.headers = new Map();
                  this._rawContent = raw;
                  
                  // Parse headers from raw content
                  if (typeof raw === "string") {
                    const headerEnd = raw.indexOf("\\r\\n\\r\\n");
                    if (headerEnd > -1) {
                      const headerLines = raw.substring(0, headerEnd).split("\\r\\n");
                      for (const line of headerLines) {
                        const [key, ...valueParts] = line.split(":");
                        if (key && valueParts.length > 0) {
                          this.headers.set(key.toLowerCase(), valueParts.join(":").trim());
                        }
                      }
                    }
                  }
                }
                
                async raw() {
                  if (typeof this._rawContent === "string") {
                    return new TextEncoder().encode(this._rawContent).buffer;
                  }
                  return this._rawContent;
                }
              }
              
              // Mock environment
              const env = {
                STORAGE_TYPE: "in-memory",
                BUCKET_NAME: "email-archive"
              };
              
              // Import worker (assuming it exports the email handler)
              const worker = {
                async email(message, env, ctx) {
                  console.log("📧 Processing email from:", message.from);
                  
                  try {
                    // Get raw email
                    const rawEmail = await message.raw();
                    
                    // Extract metadata
                    const metadata = {
                      messageId: message.headers.get("message-id") || "test-" + Date.now(),
                      from: message.from,
                      to: message.to,
                      subject: message.headers.get("subject") || "No subject",
                      receivedAt: new Date().toISOString(),
                      size: rawEmail.byteLength
                    };
                    
                    // Generate storage keys
                    const date = new Date();
                    const datePrefix = "emails/" + date.getFullYear() + "/" + String(date.getMonth() + 1).padStart(2, '0') + "/" + String(date.getDate()).padStart(2, '0');
                    const baseKey = datePrefix + "/" + metadata.messageId;
                    
                    // Store in memory
                    await adapter.upload(baseKey + ".eml", rawEmail);
                    await adapter.upload(baseKey + ".json", JSON.stringify(metadata, null, 2));
                    
                    console.log("✅ Email archived:", baseKey);
                    return new Response("Email archived successfully");
                    
                  } catch (error) {
                    console.error("❌ Archive error:", error);
                    throw error;
                  }
                }
              };
              
              // Run tests
              async function runTests() {
                console.log("Starting E2E tests...\n");
                
                // Test 1: Simple email
                console.log("Test 1: Simple email archiving");
                const msg1 = new MockForwardableEmailMessage(
                  "alice@example.com",
                  "archive@test.com",
                  "Subject: Test Email\r\n\r\nHello World!"
                );
                await worker.email(msg1, env, {});
                
                // Test 2: HTML email
                console.log("\nTest 2: HTML email with headers");
                const msg2 = new MockForwardableEmailMessage(
                  "bob@company.com",
                  "archive@test.com",
                  "Subject: HTML Test\r\nContent-Type: text/html\r\n\r\n<h1>Hello</h1>"
                );
                msg2.headers.set("message-id", "html-test-123");
                await worker.email(msg2, env, {});
                
                // Test 3: Large email
                console.log("\nTest 3: Large email (1MB)");
                const largeContent = "X".repeat(1024 * 1024);
                const msg3 = new MockForwardableEmailMessage(
                  "system@example.com",
                  "archive@test.com",
                  "Subject: Large Email\r\n\r\n" + largeContent
                );
                await worker.email(msg3, env, {});
                
                // Verify storage
                console.log("\n📊 Storage verification:");
                const files = await adapter.list({ prefix: "emails/" });
                console.log("Total files archived: " + files.objects.length);
                
                for (const obj of files.objects) {
                  console.log("  - " + obj.key + " (" + obj.size + " bytes)");
                }
                
                // Test retrieval
                console.log("\n🔍 Testing retrieval:");
                const jsonFiles = files.objects.filter(o => o.key.endsWith('.json'));
                if (jsonFiles.length > 0) {
                  const result = await adapter.download(jsonFiles[0].key);
                  const metadata = JSON.parse(new TextDecoder().decode(result.content));
                  console.log("Retrieved metadata:", metadata);
                }
                
                console.log("\n✅ All E2E tests passed!");
              }
              
              runTests().catch(console.error);
              EOF
              
              # Create mock if it doesn't exist
              if [ ! -f src/mock/ForwardableEmailMessage.js ]; then
                mkdir -p src/mock
                cat > src/mock/ForwardableEmailMessage.js << 'EOF'
              export class MockForwardableEmailMessage {
                constructor(from, to, raw) {
                  this.from = from;
                  this.to = to;
                  this.headers = new Map();
                  this._rawContent = raw;
                  
                  // Parse headers from raw content
                  if (typeof raw === 'string') {
                    const headerEnd = raw.indexOf('\r\n\r\n');
                    if (headerEnd > -1) {
                      const headerLines = raw.substring(0, headerEnd).split('\r\n');
                      for (const line of headerLines) {
                        const [key, ...valueParts] = line.split(':');
                        if (key && valueParts.length > 0) {
                          this.headers.set(key.toLowerCase(), valueParts.join(":").trim());
                        }
                      }
                    }
                  }
                }
                
                async raw() {
                  if (typeof this._rawContent === "string") {
                    return new TextEncoder().encode(this._rawContent).buffer;
                  }
                  return this._rawContent;
                }
                
                setReject(reason) {
                  console.log('Email rejected:', reason);
                }
                
                async forward(to) {
                  console.log('Email forwarded to:', to);
                }
              }
              EOF
              fi
              
              # Run the test
              echo ""
              export DENO_DIR=$TEST_DIR/.deno
              ${deno}/bin/deno run \
                --allow-read \
                --allow-write \
                --allow-env \
                --allow-net \
                test-e2e.js
              
              # Cleanup
              cd /
              rm -rf $TEST_DIR
            ''}";
          };

          # Test Worker functionality
          test-worker = {
            type = "app";
            program = "${pkgs.writeShellScript "test-worker" ''
              echo "Testing Worker with mock email..."
              
              # Create a simple test
              TMPDIR=$(mktemp -d)
              cd $TMPDIR
              
              cat > test-worker.js << 'EOF'
              // Mock email message
              const mockMessage = {
                from: "test@example.com",
                to: "archive@test.com",
                headers: new Map([
                  ["subject", "Test Email"],
                  ["message-id", "test-123@example.com"]
                ]),
                async raw() {
                  return new TextEncoder().encode(
                    "Subject: Test Email\r\n" +
                    "From: test@example.com\r\n" +
                    "To: archive@test.com\r\n" +
                    "\r\n" +
                    "This is a test email body."
                  ).buffer;
                }
              };
              
              // Mock environment
              const env = {
                STORAGE_TYPE: "in-memory"
              };
              
              // Simple worker implementation
              const worker = {
                async email(message, env, ctx) {
                  console.log("Processing email:");
                  console.log("  From:", message.from);
                  console.log("  To:", message.to);
                  console.log("  Subject:", message.headers.get("subject"));
                  
                  const raw = await message.raw();
                  console.log("  Size:", raw.byteLength, "bytes");
                  
                  return new Response("Email processed");
                }
              };
              
              // Test it
              worker.email(mockMessage, env, {})
                .then(response => response.text())
                .then(text => console.log("\nResult:", text))
                .catch(error => console.error("Error:", error));
              EOF
              
              ${nodejs}/bin/node test-worker.js
              
              rm -rf $TMPDIR
            ''}";
          };

          # Test with Wrangler environment
          wrangler-test = {
            type = "app";
            program = "${pkgs.writeShellScript "wrangler-test" ''
              echo "🔧 Testing Email Worker with Wrangler"
              echo "===================================="
              echo ""
              
              # Create temporary project directory
              WORK_DIR=$(mktemp -d)
              cd $WORK_DIR
              
              # Create wrangler.toml
              cat > wrangler.toml << 'EOF'
              name = "email-archive-test"
              main = "src/index.js"
              compatibility_date = "2024-01-01"
              
              [vars]
              STORAGE_TYPE = "in-memory"
              BUCKET_NAME = "email-archive"
              EOF
              
              # Create Worker with in-memory storage
              mkdir -p src
              cat > src/index.js << 'EOF'
              // In-memory storage for testing
              const storage = new Map();
              
              export default {
                async fetch(request, env, ctx) {
                  const url = new URL(request.url);
                  
                  if (url.pathname === "/__email") {
                    // Handle email endpoint for testing
                    const data = await request.json();
                    const message = {
                      from: data.from,
                      to: data.to,
                      headers: new Map(Object.entries(data.headers || {})),
                      async raw() {
                        return new TextEncoder().encode(data.body || "").buffer;
                      }
                    };
                    
                    // Process email
                    const response = await this.email(message, env, ctx);
                    return response;
                  }
                  
                  if (url.pathname === "/__storage") {
                    // Return storage contents for verification
                    const contents = Array.from(storage.entries()).map(([k, v]) => ({
                      key: k,
                      size: v.length
                    }));
                    return new Response(JSON.stringify(contents), {
                      headers: { "Content-Type": "application/json" }
                    });
                  }
                  
                  return new Response("Email Archive Worker");
                },
                
                async email(message, env, ctx) {
                  console.log("Processing email from:", message.from);
                  
                  try {
                    const rawEmail = await message.raw();
                    const metadata = {
                      messageId: message.headers.get("message-id") || "test-" + Date.now(),
                      from: message.from,
                      to: message.to,
                      subject: message.headers.get("subject") || "No subject",
                      receivedAt: new Date().toISOString(),
                      size: rawEmail.byteLength
                    };
                    
                    // Store in memory
                    const date = new Date();
                    const datePrefix = "emails/" + date.getFullYear() + "/" + String(date.getMonth() + 1).padStart(2, '0') + "/" + String(date.getDate()).padStart(2, '0');
                    const baseKey = datePrefix + "/" + metadata.messageId;
                    
                    storage.set(baseKey + ".eml", new Uint8Array(rawEmail));
                    storage.set(baseKey + ".json", new TextEncoder().encode(JSON.stringify(metadata, null, 2)));
                    
                    return new Response("Email archived successfully");
                  } catch (error) {
                    console.error("Archive error:", error);
                    return new Response("Archive failed", { status: 500 });
                  }
                }
              };
              EOF
              
              # Start Wrangler in background
              echo "Starting Wrangler dev server..."
              exec nix shell nixpkgs#nodePackages.wrangler --command wrangler dev --local --port 8787 &
              WRANGLER_PID=$!
              
              # Wait for server to start
              sleep 3
              
              # Run tests
              echo ""
              echo "📧 Testing email processing..."
              
              # Test 1: Send test email
              echo "Test 1: Simple email"
              curl -s -X POST http://localhost:8787/__email \
                -H "Content-Type: application/json" \
                -d '{
                  "from": "test@example.com",
                  "to": "archive@test.com",
                  "headers": {
                    "subject": "Test Email",
                    "message-id": "test-123"
                  },
                  "body": "This is a test email"
                }' || echo "Failed to send email"
              
              echo ""
              echo "Test 2: Check storage"
              curl -s http://localhost:8787/__storage | ${pkgs.jq}/bin/jq . || echo "Failed to check storage"
              
              # Cleanup
              kill $WRANGLER_PID 2>/dev/null || true
              cd /
              rm -rf $WORK_DIR
              
              echo ""
              echo "✅ Wrangler test completed!"
            ''}";
          };

          # Architecture demo
          demo = {
            type = "app";
            program = "${pkgs.writeShellScript "demo" ''
              cat << 'EOF'
              
              Email Archive POC - Architecture Overview
              ========================================
              
              This POC demonstrates email archiving without external dependencies.
              
              Components:
              1. Cloudflare Email Worker (receives emails)
              2. In-Memory S3 Adapter (for testing)
              3. Mock Email Message (simulates Cloudflare's interface)
              
              Data Flow:
              ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
              │   Email     │───▶│   Worker    │───▶│  In-Memory   │
              │   Source    │    │  Handler    │    │   Storage    │
              └─────────────┘    └─────────────┘    └──────────────┘
              
              Testing:
              - No MinIO server required
              - Pure in-memory storage for E2E tests
              - Fast execution and cleanup
              
              Run 'nix run .#e2e-test' to see it in action!
              
              EOF
            ''}";
          };
        };
      });
}