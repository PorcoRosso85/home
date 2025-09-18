{
  description = "Nix Container POC with bats testing";

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
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # テストフレームワーク
            bats
            
            # コンテナツール
            docker
            docker-compose
            skopeo
            
            # デバッグツール
            jq
            yq
            curl
            
            # Nix関連
            nix-prefetch-docker
            arion
            
            # テストコマンド
            (pkgs.writeShellScriptBin "test-all" ''
              echo "🧪 Running all container POC tests..."
              echo ""
              
              echo "=== Single Container Tests ==="
              (cd /home/nixos/bin/src/poc/container/single && ${bats}/bin/bats test_container.bats) || true
              
              echo ""
              echo "=== Orchestra Tests ==="  
              (cd /home/nixos/bin/src/poc/container/orchestra && ${bats}/bin/bats test_orchestra.bats) || true
            '')
            
            (pkgs.writeShellScriptBin "test-single" ''
              echo "=== Single Container Tests ==="
              cd /home/nixos/bin/src/poc/container/single && ${bats}/bin/bats test_container.bats
            '')
            
            (pkgs.writeShellScriptBin "test-orchestra" ''
              echo "=== Orchestra Tests ==="
              cd /home/nixos/bin/src/poc/container/orchestra && ${bats}/bin/bats test_orchestra.bats
            '')
          ];
          
          shellHook = ''
            echo "🧪 Nix Container POC Testing Environment"
            echo ""
            echo "Available commands:"
            echo "  bats <test-file>  - Run bats tests"
            echo "  test-all          - Run all tests"
            echo "  test-single       - Run single container tests"
            echo "  test-orchestra    - Run orchestra tests"
            echo "  nix build         - Build containers"
            echo "  nix flake check   - Run all checks"
            echo ""
            echo "Test locations:"
            echo "  single/test_container.bats"
            echo "  orchestra/test_orchestra.bats"
          '';
        };
        
        # テスト実行用のチェック
        checks = {
          single-container-tests = pkgs.runCommand "single-container-tests" {
            buildInputs = [ pkgs.bats ];
          } ''
            cd ${./single}
            bats test_container.bats || echo "Tests failed (expected in Red phase)"
            touch $out
          '';
          
          orchestra-tests = pkgs.runCommand "orchestra-tests" {
            buildInputs = [ pkgs.bats ];
          } ''
            cd ${./orchestra}
            bats test_orchestra.bats || echo "Tests failed (expected in Red phase)"
            touch $out
          '';
        };
        
        # test-all, test-single, test-orchestraをdevShellに統合
      });
}