# flake-parts module for readme.nix validation
{ lib, config, flake-parts-lib, inputs, ... }:

let
  inherit (lib) mkOption mkEnableOption types;
in {
  options.perSystem = flake-parts-lib.mkPerSystemOption (ps: {
    options.readme = {
      enable = mkEnableOption "readme.nix validation and documentation checks";
      
      root = mkOption {
        type = types.path;
        # Default to the consuming flake's root, not this module's path
        default = inputs.self.outPath;
        description = "Root directory to scan for readme.nix files (defaults to the consuming flake root)";
      };
      
      ignoreExtra = mkOption {
        type = types.listOf types.str;
        default = [];
        description = "Additional directories to ignore (beyond default ignore list)";
        example = [ "build" "dist" "node_modules" ];
      };
      
      policy = {
        strict = mkOption {
          type = types.bool;
          default = false;
          description = "Enable strict mode (fail on warnings)";
        };
        
        driftMode = mkOption {
          type = types.enum ["none" "warn" "strict"];
          default = "none";
          description = "Output drift detection mode";
        };
        
        failOnUnknownOutputKeys = mkOption {
          type = types.bool;
          default = false;
          description = "Fail when unknown output keys are found";
        };
      };
    };
  });

  config.perSystem = { config, pkgs, system, ... }: 
    let 
      cfg = config.readme;
      # Anchor library defaults to the consuming flake root to avoid resolving to this module's path
      flake-readme-lib = import ./core-docs.nix { inherit lib; self = { outPath = cfg.root; }; };
      
      # Default ignore patterns
      defaultIgnore = name: type:
        builtins.elem name ([
          ".git" ".direnv" "node_modules" "result" "dist" "target" ".cache"
        ] ++ cfg.ignoreExtra);
      
      # Generate documentation report  
      docsReport = flake-readme-lib.index { 
        root = cfg.root; 
        ignore = defaultIgnore;
      };
      
      reportFile = pkgs.writeText "docs-report.json" 
        (builtins.toJSON docsReport);
        
    in lib.mkIf cfg.enable {
      
      # readme-report package for consumer-side persistence
      packages.readme-report = pkgs.writeText "readme-report.json" 
        (builtins.toJSON docsReport);
      
      # Documentation validation check
      checks.readme = pkgs.runCommand "docs-lint-check"
        {
          buildInputs = [ pkgs.jq ];
          inherit reportFile;
        } ''
          set -euo pipefail
          echo "Checking documentation structure..."
          REPORT=$(cat "$reportFile")

          # Basic structure validation
          echo "$REPORT" | jq -e '.docs | type == "object"' >/dev/null
          echo "$REPORT" | jq -e '.schemaVersion == 1' >/dev/null

          # Missing readme.nix check
          MISSING=$(echo "$REPORT" | jq -r '.missingReadmes | @tsv')
          if [ -n "$MISSING" ]; then
            echo "Missing readme.nix in directories:" >&2
            echo "$MISSING" | sed 's/^/  - /' >&2
            exit 1
          fi

          # Validation errors check
          ERR_COUNT=$(echo "$REPORT" | jq -r '.errorCount')
          if [ "$ERR_COUNT" != "0" ]; then
            echo "Validation errors detected:" >&2
            echo "$REPORT" | jq -r '.reports | to_entries[] | select(.value.errors|length>0) | "\(.key):\n" + (.value.errors | map("  - " + .) | join("\n"))' >&2
            exit 1
          fi

          # Policy-based additional checks
          ${lib.optionalString cfg.policy.strict ''
          WARN_COUNT=$(echo "$REPORT" | jq -r '.warningCount')
          if [ "$WARN_COUNT" != "0" ]; then
            echo "Warnings detected (strict mode):" >&2
            echo "$REPORT" | jq -r '.reports | to_entries[] | select(.value.warnings|length>0) | "\(.key):\n" + (.value.warnings | map("  - " + .) | join("\n"))' >&2
            exit 1
          fi
          ''}

          # failOnUnknownOutputKeys policy
          ${lib.optionalString cfg.policy.failOnUnknownOutputKeys ''
          UNKNOWN_KEYS=$(echo "$REPORT" | jq -r '.reports | to_entries[] | select(.value.warnings | map(test("Unknown output keys")) | any) | .key')
          if [ -n "$UNKNOWN_KEYS" ]; then
            echo "Unknown output keys detected (failOnUnknownOutputKeys=true):" >&2
            echo "$UNKNOWN_KEYS" | sed 's/^/  - /' >&2
            exit 1
          fi
          ''}

          # driftMode policy (placeholder for future drift detection)
          ${lib.optionalString (cfg.policy.driftMode == "warn") ''
          # TODO: Implement drift detection warnings
          # DRIFT_COUNT=$(echo "$REPORT" | jq -r '.driftCount // 0')
          # if [ "$DRIFT_COUNT" != "0" ]; then
          #   echo "Warning: Output drift detected" >&2
          # fi
          ''}
          
          ${lib.optionalString (cfg.policy.driftMode == "strict") ''
          # TODO: Implement drift detection errors  
          # DRIFT_COUNT=$(echo "$REPORT" | jq -r '.driftCount // 0')
          # if [ "$DRIFT_COUNT" != "0" ]; then
          #   echo "Error: Output drift detected (strict mode)" >&2
          #   exit 1
          # fi
          ''}

          echo "✓ Documentation structure is valid"
          touch $out
        '';

      # Note: legacy docs-report package removed. Use readme-report instead.
    };
}
