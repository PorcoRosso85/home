{
  description = "Level 3 Producer - Provides command via PATH management";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Simple command that will be available in PATH
        packages.default = pkgs.writeShellScriptBin "data-processor" ''
          #!/usr/bin/env bash
          
          # Simple data processor command
          # In real implementation, this could be a Go/Rust/Python binary
          
          case "$1" in
            --version)
              echo "data-processor 1.0.0"
              ;;
            --process)
              # Read JSON from stdin, process it
              input=$(cat)
              count=$(echo "$input" | jq '.items | length')
              echo "{
                \"processed\": $count,
                \"failed\": 0,
                \"output\": $(echo "$input" | jq '.items | map({id: .id, processed: true})')
              }"
              ;;
            *)
              echo "Usage: data-processor [--version|--process]"
              exit 1
              ;;
          esac
        '';
        
        # Level 3 contract metadata
        contract = {
          version = "1.0.0";
          type = "producer";
          commands = {
            processor = {
              command = "data-processor";  # Command name only
              version = "1.0.0";
              capabilities = [ "json-processing" ];
            };
          };
          interface = {
            inputs = {
              data = {
                type = "json";
                schema = "items-array";
              };
            };
            outputs = {
              result = {
                type = "json";
                schema = "processing-result";
              };
            };
          };
          capabilities = [ "path-managed" "pure-contract" "data-transformer" ];
        };
      });
}