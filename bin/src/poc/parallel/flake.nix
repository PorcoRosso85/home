{
  description = "Parallel Processing POCs with Deno";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # 共通の開発ツール
        commonTools = with pkgs; [
          deno
          docker
          docker-compose
          curl
          jq
          httpie
          vegeta  # 負荷テストツール
          k6      # 負荷テストツール
        ];
      in
      {
        devShells = {
          # デフォルトのシェル
          default = pkgs.mkShell {
            buildInputs = commonTools;

            shellHook = ''
              echo "🚀 Parallel Processing POCs Development Environment"
              echo "=================================================="
              echo ""
              echo "📁 Current POC: $(basename $(pwd))"
              echo ""
              echo "🔧 Available tools:"
              echo "  - deno ${pkgs.deno.version}"
              echo "  - docker ${pkgs.docker.version}"
              echo "  - k6 (load testing)"
              echo "  - vegeta (load testing)"
              echo ""
              echo "📋 Common commands:"
              echo "  nix develop              - Enter development shell"
              echo "  nix develop .#test      - Enter test shell"
              echo "  nix run .#format        - Format code"
              echo "  nix run .#lint          - Lint code"
              echo ""
              echo "💡 POC-specific commands:"
              echo "  cd 01_* && deno task start"
              echo "  cd 01_* && deno task test"
              echo "  cd 01_* && deno task load-test"
              echo ""
            '';
          };

          # テスト専用シェル
          test = pkgs.mkShell {
            buildInputs = commonTools ++ (with pkgs; [
              gnuplot    # グラフ生成
              jq         # JSON処理
              yq         # YAML処理
            ]);

            shellHook = ''
              echo "🧪 Test Environment"
              echo "Running automated tests..."
              echo ""
            '';
          };
        };

        # 実行可能なアプリケーション
        apps = {
          # コードフォーマット
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format" ''
              echo "Formatting TypeScript files..."
              ${pkgs.deno}/bin/deno fmt --check=false
            ''}";
          };

          # リント
          lint = {
            type = "app";
            program = "${pkgs.writeShellScript "lint" ''
              echo "Linting TypeScript files..."
              ${pkgs.deno}/bin/deno lint
            ''}";
          };

          # 全POCのテスト実行
          test-all = {
            type = "app";
            program = "${pkgs.writeShellScript "test-all" ''
              echo "Running tests for all POCs..."
              for dir in */; do
                if [ -f "$dir/deno.json" ]; then
                  echo "Testing $dir..."
                  (cd "$dir" && ${pkgs.deno}/bin/deno task test)
                fi
              done
            ''}";
          };
        };

        # パッケージ定義（将来の拡張用）
        packages = {
          # 例: ドキュメント生成
          docs = pkgs.stdenv.mkDerivation {
            pname = "parallel-poc-docs";
            version = "1.0.0";
            src = ./.;
            
            buildPhase = ''
              echo "Generating documentation..."
              # ドキュメント生成ロジック
            '';
            
            installPhase = ''
              mkdir -p $out
              cp -r docs $out/
            '';
          };
        };
      });
}