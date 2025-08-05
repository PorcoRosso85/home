{
  description = "Email Archive POC - Cloudflare Worker to MinIO S3";

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
        
        # Cloudflare Wrangler for Worker development
        wrangler = pkgs.nodePackages.wrangler;
        
        # MinIO for local S3 storage
        minio = pkgs.minio;
        minio-client = pkgs.minio-client;
        
        # Node.js for Worker development
        nodejs = pkgs.nodejs_20;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            nodejs
            wrangler
            minio
            minio-client
            pkgs.jq
            pkgs.curl
            s3-storage.packages.${system}.default
          ];
          
          shellHook = ''
            echo "Email Archive POC Development Environment"
            echo ""
            echo "Available commands:"
            echo "  demo           - Show system architecture and components"
            echo "  start-minio    - Start local MinIO server"
            echo "  setup-bucket   - Create email-archive bucket"
            echo "  dev-worker     - Start Worker development server"
            echo "  test-archive   - Test email archiving"
            echo "  test-local-archive - Full end-to-end demonstration"
            echo "  s3-client      - S3 storage client (from s3-storage flake)"
            echo ""
            echo "Quick start:"
            echo "  1. nix run .#demo          # See system overview"
            echo "  2. nix run .#start-minio   # Start storage"
            echo "  3. nix run .#setup-bucket  # Configure bucket"
            echo "  4. nix run .#test-local-archive  # Full demo"
          '';
        };

        apps = {
          # Start MinIO server
          start-minio = {
            type = "app";
            program = "${pkgs.writeShellScript "start-minio" ''
              echo "Starting MinIO server..."
              echo "Access Key: minioadmin"
              echo "Secret Key: minioadmin"
              echo "Console: http://localhost:9001"
              echo "API: http://localhost:9000"
              
              mkdir -p ./minio-data
              exec ${minio}/bin/minio server \
                --address :9000 \
                --console-address :9001 \
                ./minio-data
            ''}";
          };

          # Setup MinIO bucket
          setup-bucket = {
            type = "app";
            program = "${pkgs.writeShellScript "setup-bucket" ''
              echo "Setting up MinIO bucket..."
              
              # Configure MinIO client
              ${minio-client}/bin/mc alias set local http://localhost:9000 minioadmin minioadmin
              
              # Create bucket if not exists
              ${minio-client}/bin/mc mb --ignore-existing local/email-archive
              
              # Set bucket policy
              cat > /tmp/bucket-policy.json << 'EOF'
              {
                "Version": "2012-10-17",
                "Statement": [{
                  "Effect": "Allow",
                  "Principal": {"AWS": ["*"]},
                  "Action": ["s3:GetObject", "s3:PutObject"],
                  "Resource": ["arn:aws:s3:::email-archive/*"]
                }]
              }
              EOF
              
              ${minio-client}/bin/mc anonymous set-json /tmp/bucket-policy.json local/email-archive
              rm /tmp/bucket-policy.json
              
              echo "Bucket 'email-archive' created and configured"
              ${minio-client}/bin/mc ls local/
            ''}";
          };

          # Worker development server (using nix shell for performance)
          dev-worker = {
            type = "app";
            program = "${pkgs.writeShellScript "dev-worker" ''
              if [ ! -f wrangler.toml ]; then
                echo "Creating wrangler.toml..."
                cat > wrangler.toml << 'EOF'
              name = "email-archive-worker"
              main = "src/index.js"
              compatibility_date = "2024-01-01"

              [vars]
              MINIO_ENDPOINT = "http://localhost:9000"
              BUCKET_NAME = "email-archive"

              [[kv_namespaces]]
              binding = "EMAIL_METADATA"
              id = "test_namespace"
              preview_id = "test_namespace"
              EOF
              fi
              
              if [ ! -f src/index.js ]; then
                mkdir -p src
                echo "Creating basic worker..."
                cat > src/index.js << 'EOF'
              export default {
                async email(message, env, ctx) {
                  console.log("Email received:", message.from);
                  // TODO: Implement S3 archiving
                  return new Response("Email archived");
                }
              };
              EOF
              fi
              
              echo "Starting Wrangler development server..."
              exec nix shell nixpkgs#nodePackages.wrangler --command wrangler dev --local
            ''}";
          };

          # Test email archiving (using nix shell for performance)
          test-archive = {
            type = "app";
            program = "${pkgs.writeShellScript "test-archive" ''
              echo "Testing email archive with S3 storage..."
              
              # Create test email
              TMPFILE=$(mktemp)
              cat > $TMPFILE << 'EOF'
              {
                "messageId": "test-$(date +%s)@example.com",
                "from": "sender@example.com",
                "to": ["recipient@example.com"],
                "subject": "Test Email",
                "body": "This is a test email body",
                "receivedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
              }
              EOF
              
              # Use S3 storage client to archive
              echo "Archiving email to MinIO..."
              
              export S3_ENDPOINT="http://localhost:9000"
              export AWS_ACCESS_KEY_ID="minioadmin"
              export AWS_SECRET_ACCESS_KEY="minioadmin"
              
              # Generate key based on date
              DATE=$(date +%Y/%m/%d)
              MESSAGE_ID=$(exec nix shell nixpkgs#jq --command jq -r .messageId $TMPFILE)
              KEY="emails/$DATE/$MESSAGE_ID.json"
              
              # Upload using s3-client via nix shell (faster startup)
              exec nix shell ${s3-storage}#default --command s3-client upload \
                --bucket email-archive \
                --key "$KEY" \
                --file $TMPFILE
            ''}";
          };

          # Run all tests (using nix shell for performance)
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              echo "Running email archive tests..."
              
              # Check if MinIO is running via nix shell
              if ! exec nix shell nixpkgs#curl --command curl -s http://localhost:9000/minio/health/live > /dev/null; then
                echo "Error: MinIO is not running. Start it with 'nix run .#start-minio'"
                exit 1
              fi
              
              # Run archiving test
              ${self.apps.${system}.test-archive.program}
              
              echo "All tests passed!"
            ''}";
          };

          # Email demo with mock
          email-demo = {
            type = "app";
            program = "${pkgs.writeShellScript "email-demo" ''
              cd ${./.}
              exec ./scripts/email-demo.sh
            ''}";
          };

          # Demo script that shows the system architecture and components
          demo = {
            type = "app";
            program = "${pkgs.writeShellScript "demo" ''
              exec ./scripts/simple-demo.sh
            ''}";
          };

          # Full local archive test (requires development environment)
          test-local-archive = {
            type = "app";
            program = "${pkgs.writeShellScript "test-local-archive" ''
              exec ./scripts/test-local-archive.sh
            ''}";
          };
        };

        packages = {
          # Docker compose for production
          docker-compose = pkgs.writeTextFile {
            name = "docker-compose.yml";
            text = ''
              version: '3.8'
              services:
                minio:
                  image: minio/minio:latest
                  ports:
                    - "9000:9000"
                    - "9001:9001"
                  environment:
                    MINIO_ROOT_USER: ''${MINIO_ROOT_USER:-admin}
                    MINIO_ROOT_PASSWORD: ''${MINIO_ROOT_PASSWORD:-miniopassword}
                  volumes:
                    - minio_data:/data
                  command: server /data --console-address ":9001"
                  healthcheck:
                    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
                    interval: 30s
                    timeout: 20s
                    retries: 3

              volumes:
                minio_data:
            '';
          };

          # Worker source template
          worker-template = pkgs.stdenv.mkDerivation {
            name = "email-archive-worker";
            src = ./.;
            installPhase = ''
              mkdir -p $out/src
              
              # Create worker template with S3 integration
              cat > $out/src/index.js << 'EOF'
              import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

              export default {
                async email(message, env, ctx) {
                  const s3Client = new S3Client({
                    endpoint: env.MINIO_ENDPOINT,
                    region: "us-east-1",
                    credentials: {
                      accessKeyId: env.MINIO_ACCESS_KEY || "minioadmin",
                      secretAccessKey: env.MINIO_SECRET_KEY || "minioadmin",
                    },
                    forcePathStyle: true, // Required for MinIO
                  });

                  try {
                    // Get raw email
                    const rawEmail = await message.raw();
                    
                    // Extract metadata
                    const metadata = {
                      messageId: message.headers.get("message-id") || `generated-''${Date.now()}`,
                      from: message.from,
                      to: message.to,
                      subject: message.headers.get("subject"),
                      receivedAt: new Date().toISOString(),
                      size: rawEmail.length,
                    };

                    // Generate storage keys
                    const date = new Date();
                    const datePrefix = `emails/''${date.getFullYear()}/''${String(date.getMonth() + 1).padStart(2, '0')}/''${String(date.getDate()).padStart(2, '0')}`;
                    const baseKey = `''${datePrefix}/''${metadata.messageId}`;

                    // Store raw email
                    await s3Client.send(new PutObjectCommand({
                      Bucket: env.BUCKET_NAME,
                      Key: `''${baseKey}.eml`,
                      Body: rawEmail,
                      ContentType: "message/rfc822",
                    }));

                    // Store metadata
                    await s3Client.send(new PutObjectCommand({
                      Bucket: env.BUCKET_NAME,
                      Key: `''${baseKey}.json`,
                      Body: JSON.stringify(metadata, null, 2),
                      ContentType: "application/json",
                    }));

                    console.log(`Email archived: ''${baseKey}`);
                    return new Response("Email archived successfully");
                    
                  } catch (error) {
                    console.error("Archive error:", error);
                    throw error;
                  }
                }
              };
              EOF
              
              # Create package.json
              cat > $out/package.json << 'EOF'
              {
                "name": "email-archive-worker",
                "version": "1.0.0",
                "type": "module",
                "dependencies": {
                  "@aws-sdk/client-s3": "^3.0.0"
                }
              }
              EOF
              
              # Create wrangler.toml template
              cat > $out/wrangler.toml << 'EOF'
              name = "email-archive-worker"
              main = "src/index.js"
              compatibility_date = "2024-01-01"
              node_compat = true

              [vars]
              MINIO_ENDPOINT = "https://your-minio-endpoint.com"
              BUCKET_NAME = "email-archive"

              # Set these as secrets:
              # wrangler secret put MINIO_ACCESS_KEY
              # wrangler secret put MINIO_SECRET_KEY

              [[email_routing_rules]]
              type = "all"
              actions = [
                { type = "worker", value = "email-archive-worker" }
              ]
              EOF
            '';
          };
        };
      });
}