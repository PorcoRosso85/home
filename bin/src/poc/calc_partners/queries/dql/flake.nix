{
  description = "SaaS Partner Calculator - DQL Cypher Queries";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # List of all DQL query files
        queryFiles = [
          "ping.cypher"
          "calculate_partner_reward.cypher"
          "calculate_network_reward.cypher"
          "simulate_reward_changes.cypher"
          "get_partner_self_dashboard.cypher"
          "get_reward_history.cypher"
          "get_partner_performance.cypher"
          "get_inactive_partners.cypher"
          "get_churn_risk_partners.cypher"
          "get_top_partners.cypher"
          "get_customer_segments.cypher"
          "project_future_rewards.cypher"
          "calculate_ltv.cypher"
          "detect_fraud_patterns.cypher"
          "generate_monthly_payment_report.cypher"
          "optimize_reward_rules.cypher"
          "calculate_partner_activity_score.cypher"
          "detect_growth_opportunities.cypher"
          "analyze_partner_retention.cypher"
          "calculate_tier_progression.cypher"
        ];
      in
      {
        packages = {
          # Package containing all query files
          queries = pkgs.stdenv.mkDerivation {
            name = "partner-calc-dql-queries";
            src = ./.;
            
            installPhase = ''
              mkdir -p $out/queries
              cp *.cypher $out/queries/
              
              # Create an index file
              cat > $out/queries/index.json <<EOF
              {
                "description": "SaaS Partner Calculator DQL Queries",
                "query_count": ${toString (builtins.length queryFiles)},
                "queries": ${builtins.toJSON queryFiles},
                "parameter_format": "$parameterName",
                "database": "KuzuDB WASM"
              }
              EOF
            '';
          };
          
          # Validation script
          validate = pkgs.writeShellScriptBin "validate-queries" ''
            echo "Validating Cypher query files..."
            for file in *.cypher; do
              if [ -f "$file" ]; then
                echo " $file"
                # Check for parameter syntax
                if grep -q '\$' "$file"; then
                  echo "  - Contains parameters"
                fi
                # Check for comments
                if head -n 1 "$file" | grep -q '^//' ; then
                  echo "  - Has header comment"
                fi
              fi
            done
            echo ""
            echo "Total queries: $(ls -1 *.cypher 2>/dev/null | wc -l)"
          '';
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            ripgrep
            jq
          ];

          shellHook = ''
            echo "=== SaaS Partner Calculator DQL Queries ==="
            echo ""
            echo "Query files available:"
            ls -1 *.cypher 2>/dev/null | head -5
            echo "... and $(ls -1 *.cypher 2>/dev/null | wc -l) total queries"
            echo ""
            echo "Commands:"
            echo "  nix run .#validate - Validate all query files"
            echo "  rg '\\\$\\w+' *.cypher - Find all parameters"
            echo "  rg 'Pain Point:' *.cypher - List all pain points addressed"
            echo ""
            echo "Parameter format: $parameterName"
            echo "Database: KuzuDB WASM (Browser-based)"
          '';
        };

        apps = {
          validate = {
            type = "app";
            program = "${self.packages.${system}.validate}/bin/validate-queries";
          };
        };
      });
}