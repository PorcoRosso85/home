{
  description = "Claude Orchestra - Integration Testing POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    # 他のPOCを依存として追加
    claude-config.url = "path:../claude_config";
    claude-sdk.url = "path:../claude_sdk";
  };

  outputs = { self, nixpkgs, flake-utils, claude-config, claude-sdk }:
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
            echo "Claude Orchestra - Integration Testing POC"
            echo ""
            echo "Commands:"
            echo "  deno test              - Run integration tests"
            echo "  nix run .#test-red     - Run TDD Red phase tests"
            echo "  nix run .#scenario-readonly  - Run readonly scenario"
            echo ""
          '';
        };
        
        apps = {
          # TDD Red フェーズテスト
          test-red = {
            type = "app";
            program = "${pkgs.writeShellScript "run-red-tests" ''
              echo "=== TDD Red Phase: Integration Tests ==="
              echo ""
              export PATH="${pkgs.deno}/bin:$PATH"
              export TEST_DIR=$(mktemp -d)
              
              # POCのパスを環境変数として設定
              export CLAUDE_CONFIG_PATH="${claude-config}"
              export CLAUDE_SDK_PATH="${claude-sdk}"
              
              cp -r ${./.}/* $TEST_DIR/
              cd $TEST_DIR
              ${pkgs.deno}/bin/deno test --allow-all --no-lock || echo "Expected failures ✓"
              rm -rf $TEST_DIR
            ''}";
          };
          
          # シナリオ: 読み取り専用
          scenario-readonly = {
            type = "app";
            program = "${pkgs.writeShellScript "scenario-readonly" ''
              echo "=== Scenario: Readonly Code Review ==="
              
              # 1. 設定生成
              echo '{"prompt": "Review this code", "mode": "readonly"}' | \
                ${claude-config}/bin/config
              
              # TODO: SDKとの統合
            ''}";
          };
        };
      });
}