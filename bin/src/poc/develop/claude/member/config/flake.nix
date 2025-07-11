{
  description = "Claude Config Pipeline POC";

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
            deno
            jq
          ];

          shellHook = ''
            echo "Claude Config Pipeline POC"
            echo ""
            echo "Commands:"
            echo "  deno test              - Run all tests"
            echo "  ./src/config.ts        - Config generation script"
            echo "  nix run .#test-red     - Run TDD Red phase tests"
            echo ""
          '';
        };
        
        apps = {
          # 個別ツール
          config = {
            type = "app";
            program = "${pkgs.writeShellScript "claude-config" ''
              ${pkgs.deno}/bin/deno run --allow-all ${./src/config.ts} "$@"
            ''}";
          };
          
          # TDD Red フェーズテスト
          test-red = {
            type = "app";
            program = "${pkgs.writeShellScript "run-red-tests" ''
              cd ${./.}
              echo "=== TDD Red Phase: Config Generation Tests ==="
              echo ""
              # PATH にdenoを追加して、子プロセスからも呼び出せるようにする
              export PATH="${pkgs.deno}/bin:$PATH"
              # 書き込み可能な場所で実行
              export TEST_DIR=$(mktemp -d)
              cp -r ${./.}/* $TEST_DIR/
              cd $TEST_DIR
              ${pkgs.deno}/bin/deno test --allow-all --no-lock && echo "All tests passed ✓" || echo "Some tests failed (Check output above)"
              rm -rf $TEST_DIR
            ''}";
          };
          
          # パイプライン例
          example-readonly = {
            type = "app";
            program = "${pkgs.writeShellScript "example-readonly" ''
              echo '{"prompt": "Review this code", "mode": "readonly"}' | \
              ${pkgs.deno}/bin/deno run --allow-all ${./src/config.ts}
            ''}";
          };
        };
      });
}