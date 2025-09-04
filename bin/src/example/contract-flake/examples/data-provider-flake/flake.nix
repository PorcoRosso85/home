{
  description = "Data Provider Flake - Provides structured data as a shared library";

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
        # Provide data as a package
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "data-provider";
          version = "1.0.0";
          
          # No source needed - we generate data
          phases = [ "installPhase" ];
          
          installPhase = ''
            mkdir -p $out/lib $out/share/data
            
            # Generate structured data (JSON)
            cat > $out/share/data/products.json <<EOF
            {
              "products": [
                {
                  "id": "prod-001",
                  "name": "Widget A",
                  "price": 29.99,
                  "category": "hardware",
                  "metadata": {
                    "weight": 0.5,
                    "dimensions": [10, 10, 5]
                  }
                },
                {
                  "id": "prod-002",
                  "name": "Widget B",
                  "price": 49.99,
                  "category": "software",
                  "metadata": {
                    "version": "2.0.0",
                    "license": "MIT"
                  }
                }
              ],
              "timestamp": "$(date -Iseconds)",
              "version": "1.0.0"
            }
            EOF
            
            # Create a simple library interface (shell script)
            cat > $out/lib/data-provider <<EOF
            #!/usr/bin/env bash
            case "\$1" in
              get-data)
                cat $out/share/data/products.json
                ;;
              get-path)
                echo "$out/share/data/products.json"
                ;;
              *)
                echo "Usage: data-provider {get-data|get-path}"
                exit 1
                ;;
            esac
            EOF
            chmod +x $out/lib/data-provider
          '';
        };
        
        # Shared library output
        lib = {
          dataPath = "${self.packages.${system}.default}/share/data/products.json";
          getData = ''
            cat ${self.packages.${system}.default}/share/data/products.json
          '';
        };
        
        # Contract metadata
        contract = {
          version = "1.0.0";
          type = "data-provider";
          outputs = {
            data = {
              format = "json";
              schema = "products";
              path = "share/data/products.json";
            };
          };
          capabilities = [ "data-source" "json" "static" ];
        };
      });
}