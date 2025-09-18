{
  description = "Flake dependency POC for dependency analysis";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs = inputs@{ self, nixpkgs, flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } ({self, ...}: {
      imports = [];

      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      perSystem = { config, self', inputs', pkgs, system, lib, ... }:
      let
        # Import the indexer functions from the separate file
        coreIndexer = import ./lib/core-indexer.nix { inherit lib self inputs; };
        # Construct minimal lock data from evaluated inputs' sourceInfo
        # Avoid embedding entire sourceInfo (which may coerce to a store path)
        manualLockData = {
          version = 7;
          root = "root";
          nodes = {
            root = {
              inputs = {
                flake-parts = "flake-parts";
                nixpkgs = "nixpkgs";
              };
            };
            flake-parts = {
              inputs = { nixpkgs-lib = "nixpkgs-lib"; };
              locked = {
                type = "github";
                owner = "hercules-ci";
                repo = "flake-parts";
                rev = inputs.flake-parts.rev or (inputs.flake-parts.sourceInfo.rev or null);
                narHash = inputs.flake-parts.narHash or (inputs.flake-parts.sourceInfo.narHash or null);
                lastModified = inputs.flake-parts.lastModified or (inputs.flake-parts.sourceInfo.lastModified or null);
              };
              original = {
                type = "github";
                owner = "hercules-ci";
                repo = "flake-parts";
              };
            };
            nixpkgs = {
              locked = {
                type = "github";
                owner = "NixOS";
                repo = "nixpkgs";
                rev = inputs.nixpkgs.rev or (inputs.nixpkgs.sourceInfo.rev or null);
                narHash = inputs.nixpkgs.narHash or (inputs.nixpkgs.sourceInfo.narHash or null);
                lastModified = inputs.nixpkgs.lastModified or (inputs.nixpkgs.sourceInfo.lastModified or null);
              };
              original = {
                type = "github";
                owner = "NixOS";
                repo = "nixpkgs";
                ref = "nixos-unstable";
              };
            };
            nixpkgs-lib = {
              locked = {
                type = "github";
                owner = "nix-community";
                repo = "nixpkgs.lib";
              };
              original = {
                type = "github";
                owner = "nix-community";
                repo = "nixpkgs.lib";
              };
            };
          };
        };
      in {
        # Package output for CI/CD
        packages.deps-json = pkgs.writeText "deps.json"
          (builtins.toJSON (coreIndexer.indexFromLock { lockData = manualLockData; }));
        
        # Default package
        packages.default = config.packages.deps-json;

        # Variant: JSON with nixpkgs skipped (to exercise skipInputs in checks)
        packages."deps-json-skip-nixpkgs" = pkgs.writeText "deps-skip-nixpkgs.json" 
          (builtins.toJSON (coreIndexer.indexFromLock { 
            lockData = manualLockData;
            skipInputs = [ "nixpkgs" ]; 
          }));
        
        # Schema validation checks
        checks.deps-schema = pkgs.runCommand "deps-schema-check" {} ''
          JSON=${config.packages.deps-json}
          
          echo "Validating schema version..."
          ${pkgs.jq}/bin/jq -e '.schemaVersion == 2' "$JSON"
          
          echo "Validating deps structure..."
          # Check all deps have required fields
          ${pkgs.jq}/bin/jq -e 'all(.deps[]; has("name") and has("node") and has("isFlake") and has("locked") and has("original"))' "$JSON"
          
          # Type-specific validation for GitHub
          echo "Validating GitHub type dependencies..."
          if ${pkgs.jq}/bin/jq -e '.deps[] | select(.locked.type=="github")' "$JSON" > /dev/null 2>&1; then
            ${pkgs.jq}/bin/jq -e '.deps[] | select(.locked.type=="github") | .locked | has("owner") and has("repo") and has("rev") and has("narHash") and has("lastModified")' "$JSON"
          fi
          
          # Type-specific validation for Path
          echo "Validating Path type dependencies..."
          if ${pkgs.jq}/bin/jq -e '.deps[] | select(.locked.type=="path")' "$JSON" > /dev/null 2>&1; then
            ${pkgs.jq}/bin/jq -e '.deps[] | select(.locked.type=="path") | .locked | has("path")' "$JSON"
          fi
          
          echo "Validating follows resolution..."
          ${pkgs.jq}/bin/jq -e '(.deps | map(select(.node==null)) | length) == 0' "$JSON"
          
          echo "Validating sort order..."
          ${pkgs.jq}/bin/jq -r '.deps[].name' "$JSON" | sort -c
          
          echo "Validating timestamp format..."
          ${pkgs.jq}/bin/jq -e '.generatedAt | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")' "$JSON"
          
          touch $out
        '';
        
        # Test skipInputs functionality (using prebuilt package variant)
        checks.skip-inputs = pkgs.runCommand "skip-inputs-check" {} ''
          JSON=${config.packages.deps-json-skip-nixpkgs}
          # Assert that "nixpkgs" does not appear in deps names
          ${pkgs.jq}/bin/jq -e '(.deps | map(.name) | index("nixpkgs")) == null' "$JSON"
          touch $out
        '';
        
        # Test pipeline composition (dependency analysis only)
        checks.pipeline-composition = pkgs.runCommand "pipeline-composition-check" {} ''
          echo "Verifying dependency analysis functionality..."
          
          # Test: Verify coreIndexer returns expected structure
          # Using embedded lockData to avoid file access issues
          DEPS='${builtins.toJSON (coreIndexer.indexFromLock { 
            lockData = manualLockData; 
          })}'
          echo "$DEPS" | ${pkgs.jq}/bin/jq -e '.deps | type == "array"'
          echo "$DEPS" | ${pkgs.jq}/bin/jq -e '.schemaVersion == 2'
          
          echo "✓ Dependency analysis functions are available and functional"
          touch $out
        '';
      };

      # Expose lib functions at flake level for external use
      flake = {
        lib = rec {
          # Core dependency analysis function - system independent
          deps = {
            # Main index function that works with lock files/data
            index = { lockPath ? null, lockData ? null, skipInputs ? [], depth ? 1 }:
              let
                # Import core indexer logic without flake-parts wrapper
                coreIndexer = import ./lib/core-indexer.nix { inherit (nixpkgs) lib; inherit self inputs; };
              in
              coreIndexer.indexFromLock { inherit lockPath lockData skipInputs depth; };
          };
        };
      };
    });
}
