{
  description = "Contract Service POC - Automatic contract matching and routing";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = with pkgs; [
        deno
        kuzu
        # Development tools
        jq
        curl
        httpie
      ];

      shellHook = ''
        echo "Contract Service POC Development Environment"
        echo "============================================"
        echo "Commands:"
        echo "  deno task dev     - Start development server"
        echo "  deno task test    - Run tests"
        echo "  deno task build   - Build for production"
        echo ""
        
        # Create deno.json if not exists
        if [ ! -f deno.json ]; then
          cat > deno.json << 'EOF'
{
  "tasks": {
    "dev": "deno run --allow-net --allow-read --allow-write --watch src/main.ts",
    "test": "deno test --allow-all",
    "build": "deno compile --allow-net --allow-read --allow-write --output=contract-service src/main.ts"
  },
  "imports": {
    "@std/": "https://deno.land/std@0.208.0/",
    "kuzu": "./src/kuzu_wrapper.ts"
  }
}
EOF
        fi
      '';
    };

    packages.${system}.default = pkgs.stdenv.mkDerivation {
      pname = "contract-service";
      version = "0.1.0";
      
      src = ./.;
      
      buildInputs = with pkgs; [ deno kuzu ];
      
      buildPhase = ''
        export DENO_DIR=$PWD/.deno
        deno compile \
          --allow-net \
          --allow-read \
          --allow-write \
          --output=contract-service \
          src/main.ts
      '';
      
      installPhase = ''
        mkdir -p $out/bin
        cp contract-service $out/bin/
      '';
    };

    apps.${system}.default = {
      type = "app";
      program = "${self.packages.${system}.default}/bin/contract-service";
    };
  };
}