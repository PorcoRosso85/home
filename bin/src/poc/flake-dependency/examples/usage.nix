# examples/usage.nix
# How to use the pipeline examples in your flake
{
  description = "Example flake using flake-dependency pipelines";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-dependency.url = "path:../";  # or github URL
  };

  outputs = { self, nixpkgs, flake-dependency }:
    let
      lib = nixpkgs.lib;
      pipelines = import ./cross-flake-pipeline.nix {
        inherit lib flake-dependency;
      };
    in {
      # Export pipeline results as packages
      packages.x86_64-linux = {
        # Path dependencies docs only
        path-docs = nixpkgs.legacyPackages.x86_64-linux.writeText "path-docs.json"
          (builtins.toJSON (pipelines.collectPathDocs {
            lockPath = ./flake.lock;
          }));
        
        # Full pipeline (without GitHub to avoid network in CI)
        full-analysis = nixpkgs.legacyPackages.x86_64-linux.writeText "full-analysis.json"
          (builtins.toJSON (pipelines.fullPipeline {
            lockPath = ./flake.lock;
            includeGithub = false;
          }));
      };
      
      # Or use in checks
      checks.x86_64-linux.pipeline-test = 
        nixpkgs.legacyPackages.x86_64-linux.runCommand "pipeline-test" {} ''
          echo "Testing pipeline composition..."
          # Verify pipeline returns expected structure
          echo '${builtins.toJSON (pipelines.collectPathDocs { 
            lockPath = ./flake.lock; 
          })}' | ${nixpkgs.legacyPackages.x86_64-linux.jq}/bin/jq -e '.pathDeps'
          touch $out
        '';
    };
}