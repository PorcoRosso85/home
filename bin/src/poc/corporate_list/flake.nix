{
  description = "企業リード収集ツール（Playwright対応）";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # パッケージ定義（Single Source of Truth）
        scrapeTools = pkgs.buildEnv {
          name = "scrape-tools";
          paths = with pkgs; [
            nodejs_22
            nodePackages.pnpm
            chromium
            jq
          ];
        };
      in
      {
        # パッケージ提供（これだけでOK！）
        packages.default = scrapeTools;
        
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs_22
            nodePackages.pnpm
            nodePackages.typescript
            chromium
            jq
          ];
          
          shellHook = ''
            export PLAYWRIGHT_BROWSERS_PATH=${pkgs.chromium}
            export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
            echo "🚀 Development environment ready!"
            echo "Available commands: node, pnpm, tsc"
            echo "Note: tsx available via npm (already installed locally)"
          '';
        };
        
        # 環境変数を含むラッパースクリプト（switchover対応）
        apps.scrape = {
          type = "app";
          program = "${pkgs.writeShellScript "scrape-with-env" ''
            export PLAYWRIGHT_BROWSERS_PATH=${pkgs.chromium}
            export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
            
            if [ ! -d node_modules ]; then
              echo "📦 Installing dependencies..."
              ${pkgs.nodePackages.pnpm}/bin/pnpm install
            fi
            
            # Use switchover script for implementation selection
            # USE_LEGACY=true uses legacy implementation, default uses TypeScript
            exec ${pkgs.nodejs_22}/bin/node scripts/switchover.mjs "$@"
          ''}";
        };
      });
}