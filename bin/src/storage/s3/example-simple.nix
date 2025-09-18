{
  description = "Minimal example using S3 storage adapter";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    s3-storage.url = "path:./"; # or "github:yourusername/s3-storage"
  };

  outputs = { self, nixpkgs, s3-storage }:
    let
      system = "x86_64-linux"; # adjust as needed
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      # Simple TypeScript script using the library
      packages.${system}.default = pkgs.writeTextDir "use-s3.ts" ''
        import { createStorageAdapter } from "${s3-storage}/mod.ts";
        
        // Use in-memory adapter for testing
        const adapter = createStorageAdapter({ type: "in-memory" });
        
        // Upload a file
        await adapter.upload("hello.txt", "Hello from flake!");
        
        // List files
        const files = await adapter.list();
        console.log("Files:", files.objects.map(f => f.key));
        
        // Download file
        const result = await adapter.download("hello.txt");
        console.log("Content:", new TextDecoder().decode(result.content));
      '';
    };
}