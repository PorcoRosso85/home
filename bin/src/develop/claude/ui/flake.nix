{
  description = "Claude launcher - development environment only";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    # 開発環境のみ定義（packages, appsは削除）
    devShells.${system}.default = pkgs.mkShell {
      packages = with pkgs; [
        # 実行に必要な依存関係
        fzf
        findutils
        coreutils
        gnugrep
        bash
        
        # 開発・テスト用
        bats
        shellcheck
        shfmt
      ];
      
      shellHook = ''
        echo "🚀 Claude Launcher Development Environment"
        echo ""
        echo "Available scripts:"
        echo "  ./claude-launcher           - Main launcher"
        echo "  ./scripts/select-project    - Project selector"
        echo "  ./scripts/launch-claude     - Claude launcher"
        echo ""
        echo "Test commands:"
        echo "  bats test_*.bats           - Run all tests"
        echo "  shellcheck scripts/*       - Lint scripts"
        echo ""
        echo "Usage examples:"
        echo "  nix develop -c ./claude-launcher"
        echo "  nix develop -c bats test_e2e_integrated.bats"
      '';
    };
  };
}