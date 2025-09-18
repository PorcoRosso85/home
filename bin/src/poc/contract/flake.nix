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
        
        # deno.json is already maintained in the repository
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

    apps.${system} = {
      default = {
        type = "app";
        program = "${pkgs.writeShellScript "entry-readme" ''
          echo "Contract Service - 自動契約締結サービス"
          echo "========================================"
          echo ""
          echo "使用方法:"
          echo "  nix run .#run < operations.json    # 操作実行"
          echo "  nix run .#test < scenarios.json    # テスト実行"
          echo "  nix run .#server                   # サーバー起動"
          echo ""
          echo "詳細: cat README.md"
        ''}";
      };
      
      run = {
        type = "app";
        program = "${pkgs.writeShellScript "entry-run" ''
          # JSON入力を処理してContract Serviceを操作
          input=$(cat)
          
          # サーバーが起動していることを確認
          if ! curl -s http://localhost:8000/health > /dev/null; then
            echo "Error: Contract Service is not running. Start with: nix run .#server"
            exit 1
          fi
          
          # JSONを解析して適切なAPIを呼び出す
          echo "$input" | ${pkgs.deno}/bin/deno eval '
            const input = JSON.parse(await Deno.readTextFile("/dev/stdin"));
            
            async function execute(op) {
              const endpoint = {
                "register_provider": "/register/provider",
                "register_consumer": "/register/consumer", 
                "call_service": "/call",
                "check_contracts": "/contracts/" + (op.consumer || ""),
                "register_transform": "/transform/register"
              }[op.operation];
              
              const method = op.operation === "check_contracts" ? "GET" : "POST";
              const body = method === "POST" ? JSON.stringify(op.data || op) : undefined;
              
              const res = await fetch("http://localhost:8000" + endpoint, {
                method,
                headers: { "Content-Type": "application/json" },
                body
              });
              
              console.log(await res.json());
            }
            
            if (Array.isArray(input)) {
              for (const op of input) await execute(op);
            } else {
              await execute(input);
            }
          '
        ''}";
      };
      
      test = {
        type = "app";
        program = "${pkgs.writeShellScript "entry-test" ''
          # Run tests in current directory, not in nix store
          exec ${pkgs.deno}/bin/deno test --allow-all test/integration/
        ''}";
      };
      
      server = {
        type = "app";
        program = "${pkgs.writeShellScript "server" ''
          cd ${./.}
          exec ${pkgs.deno}/bin/deno run --allow-net --allow-read --allow-write src/main.ts
        ''}";
      };
    };
  };
}