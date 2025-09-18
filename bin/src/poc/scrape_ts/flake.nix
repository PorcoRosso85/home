{
  description = "Scraper packages - 汎用スクレイピングツール群";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Node.js環境
        nodejs = pkgs.nodejs_22;
        
        # Bun環境
        bunEnv = pkgs.bun;
        
        # 開発用ツール
        devTools = with pkgs; [
          nodejs
          bunEnv
          nodePackages.typescript
          nodePackages.pnpm
          chromium  # Playwright用
          jq
        ];
        
        # シンプルなソースパッケージとして提供（ビルド不要）
        scraperCore = pkgs.stdenv.mkDerivation {
          pname = "scraper-core";
          version = "1.0.0";
          src = ./scraper-core;
          
          installPhase = ''
            mkdir -p $out
            cp -r . $out
          '';
        };
        
        # scraper-prtimesパッケージ
        scraperPrtimes = pkgs.stdenv.mkDerivation {
          pname = "scraper-prtimes";
          version = "1.0.0";
          src = ./scraper-prtimes;
          
          installPhase = ''
            mkdir -p $out
            cp -r . $out
          '';
        };
        
      in
      {
        # パッケージとして提供
        packages = {
          default = scraperCore;
          scraper-core = scraperCore;
          scraper-prtimes = scraperPrtimes;
          
          # 統合パッケージ（両方を含む）
          all = pkgs.buildEnv {
            name = "scraper-all";
            paths = [ scraperCore scraperPrtimes ];
          };
        };
        
        # Overlayとして提供（他のflakeから利用可能）
        overlays.default = final: prev: {
          scraperCore = scraperCore;
          scraperPrtimes = scraperPrtimes;
        };
        
        # 開発シェル
        devShells.default = pkgs.mkShell {
          buildInputs = devTools;
          
          shellHook = ''
            echo "🚀 Scraper Development Environment"
            echo "Available packages:"
            echo "  - scraper-core: Generic scraping utilities"
            echo "  - scraper-prtimes: PR Times specific scraper"
            echo ""
            echo "Commands:"
            echo "  nix build .#scraper-core  - Build core package"
            echo "  nix build .#scraper-prtimes - Build PR Times package"
            echo "  nix develop - Enter development shell"
          '';
        };
        
        # アプリケーション（実行可能）
        apps = {
          # テスト実行
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test-all" ''
              echo "Running tests for all packages..."
              cd ${./.}
              ${bunEnv}/bin/bun test
            ''}";
          };
          
          # READMEの表示
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              cat ${./README.md}
            ''}";
          };
        };
      });
}