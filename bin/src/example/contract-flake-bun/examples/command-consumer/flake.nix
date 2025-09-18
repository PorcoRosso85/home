{
  description = "Command Consumer - Uses producer command via buildInputs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    # In real usage: producer.url = "github:org/command-producer";
    # For demo, we'll use local absolute path
    producer.url = "path:/home/nixos/bin/src/example/contract-flake/examples/command-producer";
  };

  outputs = { self, nixpkgs, flake-utils, producer }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "command-consumer";
          version = "1.0.0";
          
          # Command-based: Producer command automatically in PATH
          buildInputs = [
            producer.packages.${system}.default
            pkgs.bun
            pkgs.jq
          ];
          
          src = ./.;
          
          buildPhase = ''
            # Bundle the TypeScript consumer for Node.js target
            cp ${./consumer.ts} consumer.ts
            bun build consumer.ts --target node --outfile dist/consumer.js
          '';
          
          installPhase = ''
            mkdir -p $out/bin
            
            # Create runner script with producer in PATH
            cat > $out/bin/command-consumer << EOF
            #!/usr/bin/env bash
            # Command-based: data-processor is in PATH via buildInputs
            export PATH="${producer.packages.${system}.default}/bin:\$PATH"
            exec ${pkgs.bun}/bin/bun run $out/lib/consumer.js "\$@"
            EOF
            chmod +x $out/bin/command-consumer
            
            # Install the bundle
            mkdir -p $out/lib
            cp dist/consumer.js $out/lib/
          '';
        };
        
        # Command-based contract metadata
        contract = {
          version = "1.0.0";
          type = "consumer";
          commands = {
            processor = {
              command = "data-processor";  # Same name, no path
              version = "1.0.0";
              capabilities = [ "json-processing" ];
            };
          };
          interface = {
            inputs = {
              rawData = {
                type = "array";
                schema = "items";
              };
            };
            outputs = {
              report = {
                type = "json";
                schema = "summary";
              };
            };
          };
          capabilities = [ "path-managed" "pure-contract" "data-consumer" ];
        };
      });
}