{
  description = "Example flake using S3 storage adapter as input";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    # Reference the S3 storage adapter flake
    s3-storage = {
      url = "path:./"; # In real usage: "github:yourusername/s3-storage"
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, s3-storage }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        deno = pkgs.deno;
      in
      {
        # Example 1: Use S3 storage in a TypeScript/Deno application
        packages.backup-tool = pkgs.writeTextDir "backup-tool.ts" ''
          import { createStorageAdapter, S3StorageApplication } from "${s3-storage}/mod.ts";
          
          // Create adapter using environment variables
          const adapter = createStorageAdapter({
            type: "s3",
            endpoint: Deno.env.get("S3_ENDPOINT") || "https://s3.amazonaws.com",
            region: Deno.env.get("AWS_REGION") || "us-east-1",
            accessKeyId: Deno.env.get("AWS_ACCESS_KEY_ID") || "",
            secretAccessKey: Deno.env.get("AWS_SECRET_ACCESS_KEY") || "",
            bucket: Deno.env.get("S3_BUCKET") || "my-backup-bucket"
          });
          
          // Backup function
          export async function backup(files: Record<string, string>) {
            for (const [name, content] of Object.entries(files)) {
              const key = `backups/''${new Date().toISOString()}/''${name}`;
              await adapter.upload(key, content);
              console.log(`Backed up: ''${key}`);
            }
          }
          
          // Restore function
          export async function restore(date: string) {
            const prefix = `backups/''${date}/`;
            const result = await adapter.list({ prefix });
            
            const restored: Record<string, string> = {};
            for (const obj of result.objects) {
              const download = await adapter.download(obj.key);
              const filename = obj.key.replace(prefix, "");
              restored[filename] = new TextDecoder().decode(download.content);
            }
            return restored;
          }
        '';

        # Example 2: CLI wrapper using the S3 client
        packages.s3-wrapper = pkgs.writeShellScriptBin "s3-wrapper" ''
          # Use the S3 client from the input flake
          exec ${s3-storage.packages.${system}.default}/bin/s3-client "$@"
        '';

        # Example 3: Development environment with S3 storage library
        devShells.default = pkgs.mkShell {
          buildInputs = [ deno ];
          
          shellHook = ''
            echo "Development environment with S3 storage adapter"
            echo "S3 storage library available at: ${s3-storage}"
            echo ""
            echo "Example usage:"
            echo "  import { createStorageAdapter } from '${s3-storage}/mod.ts';"
          '';
        };

        # Example 4: Application that uses S3 storage
        apps.backup-app = {
          type = "app";
          program = "${pkgs.writeShellScript "backup-app" ''
            export DENO_DIR=$(mktemp -d)
            cd ${self.packages.${system}.backup-tool}
            
            cat << 'EOF' | ${deno}/bin/deno run --allow-all -
            import { backup, restore } from "./backup-tool.ts";
            
            // Example usage
            await backup({
              "config.json": JSON.stringify({ version: "1.0" }),
              "data.txt": "Important data to backup"
            });
            
            console.log("Backup completed!");
            EOF
          ''}";
        };
      });
}