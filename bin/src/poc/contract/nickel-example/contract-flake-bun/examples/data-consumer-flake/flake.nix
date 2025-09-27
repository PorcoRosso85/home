{
  description = "Data Consumer Flake - Consumes and processes structured data";

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
        # Package that consumes data
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "data-consumer";
          version = "1.0.0";
          
          buildInputs = with pkgs; [ jq ];
          
          phases = [ "installPhase" ];
          
          installPhase = ''
            mkdir -p $out/bin $out/lib
            
            # Create consumer script (uses jq for JSON processing)
            cat > $out/bin/data-consumer <<EOF
            #!/usr/bin/env bash
            
            DATA_PATH="\$1"
            OPERATION="\$2"
            
            if [ -z "\$DATA_PATH" ] || [ -z "\$OPERATION" ]; then
              echo "Usage: data-consumer <data-path> {summarize|filter-category|calculate-total}"
              exit 1
            fi
            
            case "\$OPERATION" in
              summarize)
                ${pkgs.jq}/bin/jq '{
                  total_products: .products | length,
                  categories: [.products[].category] | unique,
                  total_value: [.products[].price] | add,
                  timestamp: .timestamp
                }' "\$DATA_PATH"
                ;;
              filter-category)
                CATEGORY="\$3"
                if [ -z "\$CATEGORY" ]; then
                  echo "Category required for filter operation"
                  exit 1
                fi
                ${pkgs.jq}/bin/jq --arg cat "\$CATEGORY" '.products | map(select(.category == \$cat))' "\$DATA_PATH"
                ;;
              calculate-total)
                ${pkgs.jq}/bin/jq '[.products[].price] | add' "\$DATA_PATH"
                ;;
              *)
                echo "Unknown operation: \$OPERATION"
                exit 1
                ;;
            esac
            EOF
            chmod +x $out/bin/data-consumer
            
            # Library interface
            cat > $out/lib/consumer-lib <<EOF
            #!/usr/bin/env bash
            export CONSUMER_BIN="$out/bin/data-consumer"
            
            process_data() {
              local data_path="\$1"
              local operation="\$2"
              shift 2
              "\$CONSUMER_BIN" "\$data_path" "\$operation" "\$@"
            }
            EOF
            chmod +x $out/lib/consumer-lib
          '';
        };
        
        # Library exports
        lib = {
          consumerBin = "${self.packages.${system}.default}/bin/data-consumer";
          processData = dataPath: operation: ''
            ${self.packages.${system}.default}/bin/data-consumer ${dataPath} ${operation}
          '';
        };
        
        # Contract metadata
        contract = {
          version = "1.0.0";
          type = "data-consumer";
          inputs = {
            data = {
              format = "json";
              schema = "products";
              required = true;
            };
          };
          outputs = {
            summary = {
              format = "json";
              operations = [ "summarize" "filter-category" "calculate-total" ];
            };
          };
          capabilities = [ "data-processor" "json" "jq" ];
        };
      });
}