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
            bun
            chromium
            jq
          ];
          
          shellHook = ''
            export PLAYWRIGHT_BROWSERS_PATH=${pkgs.chromium}
            export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
            echo "🚀 Development environment ready!"
            echo "Available commands: node, pnpm, tsc, bun"
            echo "Note: Migrating from Node.js to Bun for native TypeScript execution"
          '';
        };
        
        # Bunによる直接実行
        apps.scrape = {
          type = "app";
          program = "${pkgs.writeShellScript "scrape-with-bun" ''
            export PLAYWRIGHT_BROWSERS_PATH=${pkgs.chromium}
            export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
            
            if [ ! -f bun.lock ]; then
              echo "📦 Installing dependencies with Bun..."
              ${pkgs.bun}/bin/bun install
            fi
            
            # Run TypeScript directly with Bun
            exec ${pkgs.bun}/bin/bun run src/main.ts "$@"
          ''}";
        };
      });
}