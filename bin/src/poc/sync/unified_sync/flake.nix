{
  description = "Unified Sync - KuzuDB WASM + WebSocket + Event Store";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # プロジェクトファイル
        # 
        # Nixビルド環境の制約:
        # - ビルド時はネットワークアクセス禁止
        # - npm installがビルド時に実行できない
        # 
        # 改善策（実装済み）:
        # - ~/.cache/unified-sync-test にnode_modulesをキャッシュ
        # - package.jsonが変更された時のみnpm install実行
        # - 2回目以降は既存のnode_modulesを再利用（高速）
        #
        # 理想的な解決策（将来）:
        # - npmPackage, yarn2nix, node2nixなどを使用
        # - 事前にパッケージをダウンロードしてNixビルド
        projectFiles = pkgs.stdenv.mkDerivation {
          name = "unified-sync-files";
          src = ./.;
          installPhase = ''
            mkdir -p $out
            cp -r * $out/
          '';
        };
        
        # テストスクリプト
        testScript = pkgs.writeShellScriptBin "test-sync" ''
          #!${pkgs.bash}/bin/bash
          set -e
          
          echo "🧪 KuzuDB Multi-Browser Sync Tests"
          echo "================================"
          
          # 環境変数設定
          export PATH=${pkgs.deno}/bin:${pkgs.nodejs_20}/bin:$PATH
          export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=${pkgs.chromium}/bin/chromium
          export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
          
          # Chromium用の環境変数
          export FONTCONFIG_PATH=${pkgs.fontconfig}/etc/fonts
          export FONTCONFIG_FILE=${pkgs.fontconfig}/etc/fonts/fonts.conf
          
          # キャッシュディレクトリを使用（毎回削除しない）
          CACHE_DIR="$HOME/.cache/unified-sync-test"
          mkdir -p "$CACHE_DIR"
          
          # 作業ディレクトリ作成（node_modulesは共有）
          WORK_DIR=$(mktemp -d)
          trap "rm -rf $WORK_DIR" EXIT
          
          echo "📁 Preparing test environment..."
          
          # プロジェクトファイルをコピー
          cp -r ${projectFiles}/* $WORK_DIR/
          
          # 書き込み権限を付与
          chmod -R u+w $WORK_DIR
          
          cd $WORK_DIR
          
          # デバッグ: ファイル確認
          echo "📂 Files in work directory:"
          ls -la | head -20
          echo ""
          echo "📂 Files in e2e directory:"
          ls -la e2e/ || echo "No e2e directory found"
          echo ""
          
          # package.jsonを作成
          cat > package.json << 'EOF'
          {
            "name": "unified-sync",
            "type": "module",
            "devDependencies": {
              "@playwright/test": "^1.40.0",
              "@types/node": "^20.0.0"
            },
            "dependencies": {
              "kuzu-wasm": "^0.0.10"
            }
          }
          EOF
          
          # package.jsonが変更されているかチェック
          if [ ! -f "$CACHE_DIR/package.json" ] || ! diff -q package.json "$CACHE_DIR/package.json" > /dev/null 2>&1; then
            echo "📦 Installing dependencies (package.json changed or first run)..."
            # キャッシュディレクトリでインストール
            cp package.json "$CACHE_DIR/"
            cd "$CACHE_DIR"
            npm install --silent
            cd "$WORK_DIR"
            # node_modulesをコピー
            cp -r "$CACHE_DIR/node_modules" node_modules
          else
            echo "✅ Dependencies up to date"
            # キャッシュからnode_modulesをコピー
            if [ -d "$CACHE_DIR/node_modules" ]; then
              cp -r "$CACHE_DIR/node_modules" node_modules
            fi
          fi
          
          # playwright.configを作成
          cat > playwright.config.ts << 'EOF'
          import { defineConfig } from '@playwright/test';
          
          export default defineConfig({
            testDir: './e2e',
            testMatch: 'test-all.spec.ts',
            timeout: 60000,
            use: {
              browserName: 'chromium',
              headless: true,
              launchOptions: {
                executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
                args: [
                  '--no-sandbox',
                  '--disable-setuid-sandbox',
                  '--disable-dev-shm-usage',
                  '--enable-features=SharedArrayBuffer',
                  '--enable-features=WebAssemblyThreads'
                ]
              },
            },
            reporter: [['list']]
          });
          EOF
          
          # ブラウザ依存関係を正しく設定
          export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [
            pkgs.glib
            pkgs.nss
            pkgs.nspr
            pkgs.atk
            pkgs.gtk3
            pkgs.pango
            pkgs.cairo
            pkgs.gdk-pixbuf
            pkgs.xorg.libX11
            pkgs.xorg.libxcb
            pkgs.xorg.libXcomposite
            pkgs.xorg.libXcursor
            pkgs.xorg.libXdamage
            pkgs.xorg.libXext
            pkgs.xorg.libXfixes
            pkgs.xorg.libXi
            pkgs.xorg.libXrandr
            pkgs.xorg.libXrender
            pkgs.xorg.libXtst
            pkgs.xorg.libxshmfence
            pkgs.mesa
            pkgs.alsa-lib
            pkgs.libpulseaudio
            pkgs.cups
            pkgs.libdrm
            pkgs.dbus
            pkgs.expat
            pkgs.fontconfig
            pkgs.freetype
            pkgs.libudev0-shim
            pkgs.libxkbcommon
            pkgs.at-spi2-atk
            pkgs.at-spi2-core
            pkgs.libGL
            pkgs.libGLU
            pkgs.zlib
            pkgs.gcc.cc.lib
          ]}:$LD_LIBRARY_PATH
          
          # node_modulesが正しくリンクされているか確認
          if [ ! -d node_modules ]; then
            echo "❌ node_modules not found!"
            exit 1
          fi
          
          # Xvfbを使ってヘッドレス環境でテスト実行
          echo ""
          echo "🚀 Running integrated E2E test..."
          ${pkgs.xvfb-run}/bin/xvfb-run -a ${pkgs.nodejs_20}/bin/npx playwright test
          
          TEST_RESULT=$?
          
          if [ $TEST_RESULT -eq 0 ]; then
            echo ""
            echo "✅ All tests passed!"
            echo ""
            echo "🎆 KuzuDB Multi-Browser Sync is working perfectly!"
          else
            echo ""
            echo "❌ Tests failed"
            exit 1
          fi
        '';
        
      in
      {
        # テスト実行用アプリ
        apps.test = {
          type = "app";
          program = "${testScript}/bin/test-sync";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Deno for server and tests
            deno
            
            # Node.js for KuzuDB WASM compatibility
            nodejs_20
            nodePackages.pnpm
            
            # Playwright for E2E browser tests
            chromium
            xvfb-run
            
            # Development tools
            jq
            curl
            websocat  # WebSocket testing
          ];

          shellHook = ''
            echo "🔄 Unified Sync Development Environment"
            echo "====================================="
            echo ""
            echo "📦 Available tools:"
            echo "  - Deno ${pkgs.deno.version}"
            echo "  - Node.js ${pkgs.nodejs_20.version}"
            echo "  - pnpm (ESM package manager)"
            echo "  - Chromium (for Playwright)"
            echo "  - websocat (WebSocket testing)"
            echo ""
            
            # E2Eテストコマンド
            e2e() {
              echo "🧪 Running E2E tests..."
              npx playwright test "$@"
            }
            
            e2e-ui() {
              echo "🎭 Running E2E tests with UI..."
              npx playwright test --ui "$@"
            }
            
            e2e-debug() {
              echo "🐛 Debugging E2E tests..."
              npx playwright test --debug "$@"
            }
            
            echo "🧪 Test commands:"
            echo "  deno test                    - Run unit tests"
            echo "  e2e                         - Run E2E tests (headless)"
            echo "  e2e-ui                      - Run E2E tests with UI"
            echo "  e2e-debug                   - Debug E2E tests"
            echo "  deno run --allow-all server.ts - Start server"
            echo ""
            
            # Playwright executable path
            export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=${pkgs.chromium}/bin/chromium
            export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
          '';
        };
      });
}