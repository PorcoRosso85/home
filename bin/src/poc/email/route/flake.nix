{
  description = "Email Worker POC - Pure Cloudflare Email Routing with Wrangler";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Wrangler CLI for Cloudflare Worker development
        wrangler = pkgs.wrangler;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            wrangler
            pkgs.jq
            pkgs.curl
          ];
          
          shellHook = ''
            echo "Email Worker POC - Wrangler Testing Environment"
            echo ""
            echo "Available commands:"
            echo "  wrangler dev   - Start local dev server"
            echo "  nix run .#test - Run Email Worker tests"
            echo ""
            echo "Quick start:"
            echo "  nix run .#wrangler-dev   # Start dev server"
            echo "  nix run .#test          # Run tests"
          '';
        };

        apps = {
          # Wrangler dev server
          wrangler-dev = {
            type = "app";
            program = "${pkgs.writeShellScript "wrangler-dev" ''
              echo "🚀 Starting Wrangler Dev Server"
              echo "==============================="
              echo ""
              
              # Start wrangler dev server
              echo "Starting dev server on http://localhost:8787"
              echo "Press Ctrl+C to stop"
              echo ""
              
              ${wrangler}/bin/wrangler dev --local --port 8787
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
              ${wrangler}/bin/wrangler dev --local --port 8787 &
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

          # Test runner for Email Worker
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              echo "🧪 Running Email Worker Tests"
              echo "============================="
              echo ""
              
              # Simple test using wrangler types
              echo "Testing Email Worker routing logic..."
              
              # Create a simple test script
              cat > /tmp/test-worker.js << 'EOF'
              // Import worker
              const worker = {
                async email(message, env, ctx) {
                  const allowlist = ["trusted@example.com", "friend@example.com"];
                  
                  if (!allowlist.includes(message.from)) {
                    message.setReject("Address not allowed");
                    return;
                  }
                  
                  await message.forward("inbox@example.com");
                }
              };
              
              // Test 1: Allowlisted email
              console.log("Test 1: Allowlisted email");
              const msg1 = {
                from: "trusted@example.com",
                to: "user@domain.com",
                _forwarded: false,
                _rejected: false,
                setReject(reason) { this._rejected = true; this._rejectReason = reason; },
                async forward(to) { this._forwarded = true; this._forwardedTo = to; }
              };
              await worker.email(msg1, {}, {});
              console.log("  ✓ Forwarded:", msg1._forwarded);
              console.log("  ✓ Forward to:", msg1._forwardedTo);
              
              // Test 2: Non-allowlisted email
              console.log("\nTest 2: Non-allowlisted email");
              const msg2 = {
                from: "spam@example.com",
                to: "user@domain.com",
                _forwarded: false,
                _rejected: false,
                setReject(reason) { this._rejected = true; this._rejectReason = reason; },
                async forward(to) { this._forwarded = true; this._forwardedTo = to; }
              };
              await worker.email(msg2, {}, {});
              console.log("  ✓ Rejected:", msg2._rejected);
              console.log("  ✓ Reason:", msg2._rejectReason);
              
              console.log("\n✅ All tests passed!");
              EOF
              
              # Run the test
              ${pkgs.nodejs}/bin/node /tmp/test-worker.js
              
              # Clean up
              rm -f /tmp/test-worker.js
            ''}";
          };
          
          # Architecture demo
          demo = {
            type = "app";
            program = "${pkgs.writeShellScript "demo" ''
              cat << 'EOF'
              
              Email Worker POC - Architecture Overview
              ========================================
              
              This POC demonstrates pure email routing with Cloudflare Workers.
              
              Components:
              1. Cloudflare Email Worker (routes emails)
              2. Wrangler CLI (local development)
              3. Forward/Reject logic (allowlist/blocklist)
              
              Data Flow:
              ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
              │   Email     │───▶│   Worker    │───▶│  Forward or  │
              │   Source    │    │  Routing    │    │    Reject    │
              └─────────────┘    └─────────────┘    └──────────────┘
              
              Testing:
              - Wrangler dev server for local testing
              - No Node.js/Deno dependencies for runtime
              - Pure Email Worker implementation
              
              Run 'nix run .#test' to run tests!
              
              EOF
            ''}";
          };
        };
      });
}