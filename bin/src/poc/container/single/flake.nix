{
  description = "Single Flake Multi-Container Builder";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    # 外部flake参照の例
    # GitHub形式の参照（numtideのdevshellを使用）
    external-devshell = {
      url = "github:numtide/devshell";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    
    # Path形式の参照（親ディレクトリのorchestraを参照）
    external-orchestra = {
      url = "path:../orchestra";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs = { self, nixpkgs, flake-utils, external-devshell, external-orchestra }@inputs:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Node.jsアプリケーション定義
        nodejsApp = pkgs.writeShellScriptBin "nodejs-app" ''
          #!/usr/bin/env bash
          echo "Node.js Application Container"
          echo "Node version: $(${pkgs.nodejs_20}/bin/node --version)"
          echo "NPM version: $(${pkgs.nodejs_20}/bin/npm --version)"
          
          if [ "$1" = "serve" ]; then
            echo "const http = require('http');" > /tmp/server.js
            echo "http.createServer((req, res) => {" >> /tmp/server.js
            echo "  res.writeHead(200, {'Content-Type': 'text/plain'});" >> /tmp/server.js
            echo "  res.end('Hello from Node.js Nix container!');" >> /tmp/server.js
            echo "}).listen(8080);" >> /tmp/server.js
            echo "console.log('Server running at http://localhost:8080/');" >> /tmp/server.js
            ${pkgs.nodejs_20}/bin/node /tmp/server.js
          fi
        '';
        
        # Pythonアプリケーション定義
        pythonApp = pkgs.writeShellScriptBin "python-app" ''
          #!/usr/bin/env bash
          echo "Python Application Container"
          echo "Python version: $(${pkgs.python3}/bin/python3 --version)"
          
          if [ "$1" = "serve" ]; then
            echo "Starting Python HTTP server on port 8080..."
            ${pkgs.python3}/bin/python3 -m http.server 8080
          fi
        '';
        
        # Goアプリケーション定義
        goApp = pkgs.writeShellScriptBin "go-app" ''
          #!/usr/bin/env bash
          echo "Go Application Container"
          echo "Go version: $(${pkgs.go}/bin/go version)"
          
          if [ "$1" = "serve" ]; then
            cat > /tmp/server.go << 'EOF'
          package main
          import (
            "fmt"
            "net/http"
          )
          func main() {
            http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
              fmt.Fprintf(w, "Hello from Go Nix container!")
            })
            fmt.Println("Server running at http://localhost:8080/")
            http.ListenAndServe(":8080", nil)
          }
          EOF
            ${pkgs.go}/bin/go run /tmp/server.go
          fi
        '';
        
        # 共通のベースアプリケーション
        baseApp = pkgs.writeShellScriptBin "entrypoint.sh" ''
          #!/usr/bin/env bash
          echo "Single Flake Multi-Container Builder"
          echo "Available tools:"
          which curl && echo "- curl: $(curl --version | head -n1)"
          which jq && echo "- jq: $(jq --version)"
          which bash && echo "- bash: $(bash --version | head -n1)"
        '';
        
        # 外部flakeからのパッケージ収集関数（型安全）
        collectExternalPackages = flake: system:
          if flake ? packages.${system} then
            if flake.packages.${system} ? default then
              [ flake.packages.${system}.default ]
            else
              []
          else
            [];
            
        # コンテナビルド関数
        buildContainer = { name, app, runtime ? [], extraPaths ? [] }: 
          pkgs.dockerTools.buildImage {
            inherit name;
            tag = "latest";
            
            copyToRoot = pkgs.buildEnv {
              name = "${name}-root";
              paths = with pkgs; [
                bashInteractive
                coreutils
                curl
                jq
                netcat
                which
                gnugrep   # grepコマンドを追加
                app
              ] ++ runtime ++ extraPaths;
              pathsToLink = [ "/bin" "/etc" "/lib" ];
            };
            
            config = {
              Entrypoint = [ "/bin/${app.name}" ];
              Env = [
                "NIX_CONTAINER=true"
                "PATH=/bin"
                "LANG=C.UTF-8"
              ];
              ExposedPorts = {
                "8080/tcp" = {};
              };
              WorkingDir = "/";
              Labels = {
                "org.nixos.container" = "true";
                "org.nixos.description" = "Single flake multi-container system";
                "org.nixos.container-type" = name;
              };
            };
          };
      in
      {
        # 単一flakeから複数タイプのコンテナイメージをビルド
        packages = {
          # Node.jsベースのコンテナ
          container-nodejs = buildContainer {
            name = "nodejs-container";
            app = nodejsApp;
            runtime = [ pkgs.nodejs_20 ];
          };
          
          # Pythonベースのコンテナ
          container-python = buildContainer {
            name = "python-container";
            app = pythonApp;
            runtime = [ pkgs.python3 ];
          };
          
          # Goベースのコンテナ
          container-go = buildContainer {
            name = "go-container";
            app = goApp;
            runtime = [ pkgs.go ];
          };
          
          # 基本コンテナ（元の実装を保持）
          container-base = buildContainer {
            name = "base-container";
            app = baseApp;
          };
          
          # 外部flakeを統合したコンテナ（機能強化版）
          container-integrated = buildContainer {
            name = "integrated-container";
            app = pkgs.writeShellScriptBin "integrated-entrypoint.sh" ''
              #!/usr/bin/env bash
              echo "=== Integrated Container with External Flakes ==="
              echo "Built from single flake with multi-flake integration"
              echo ""
              
              echo "Available components:"
              echo "1. Base system tools:"
              which bash >/dev/null && echo "   - bash: $(bash --version | head -n1 | cut -d' ' -f4)"
              which curl >/dev/null && echo "   - curl: $(curl --version | head -n1 | cut -d' ' -f2)"
              which jq >/dev/null && echo "   - jq: $(jq --version)"
              
              echo ""
              echo "2. External flake integrations:"
              
              # external-devshellからのコマンドをチェック
              if command -v devshell-menu >/dev/null 2>&1; then
                echo "   ✓ devshell tools available"
                echo "     - devshell-menu command found"
              else
                echo "   - devshell tools: checking for components..."
                # パッケージ内容をリスト
                ls /bin/ | grep -E "devshell|mkShell" || echo "     (no devshell binaries detected)"
              fi
              
              # external-orchestraからのコンポーネントをチェック
              if [ -d "/orchestra" ]; then
                echo "   ✓ orchestra components available in /orchestra"
                ls /orchestra/ 2>/dev/null | head -5 | sed 's/^/     - /'
              else
                echo "   - orchestra components: checking for binaries..."
                # orchestraキーワードを含むバイナリを探す
                ls /bin/ | grep -i orchestra || echo "     (no orchestra binaries detected)"
              fi
              
              echo ""
              echo "3. Container layer information:"
              echo "   - Container type: integrated-container"
              echo "   - Built with: buildContainer function"
              echo "   - Layer strategy: single-flake + external-packages"
              
              echo ""
              echo "4. Runtime environment:"
              echo "   - Working directory: $(pwd)"
              echo "   - Available packages in PATH:"
              echo "     $(echo $PATH | tr ':' '\n' | wc -l) paths configured"
              
              echo ""
              echo "=== Integration Complete ==="
              
              # 引数に基づいた追加動作
              case "''${1:-}" in
                "info")
                  echo ""
                  echo "=== Detailed Information ==="
                  echo "All binaries in /bin/:"
                  ls -la /bin/ | head -20
                  ;;
                "test")
                  echo ""
                  echo "=== Integration Test ==="
                  echo "Testing basic functionality..."
                  bash --version >/dev/null && echo "✓ bash works"
                  curl --version >/dev/null && echo "✓ curl works" 
                  jq --version >/dev/null && echo "✓ jq works"
                  echo "✓ Integration test complete"
                  ;;
                *)
                  echo "Usage: container [info|test]"
                  echo "Run without arguments for summary."
                  ;;
              esac
            '';
            runtime = [
              # 統合コンテナ専用の追加ランタイム
              pkgs.file    # ファイル形式判定
              pkgs.tree    # ディレクトリ構造表示
              pkgs.htop    # プロセス監視
              pkgs.ncdu    # ディスク使用量確認
            ];
            extraPaths = 
              # 型安全なパッケージ収集関数を使用して外部flakeを統合
              (collectExternalPackages external-devshell system) ++
              (collectExternalPackages external-orchestra system);
          };
          
          # デフォルトは基本コンテナ
          default = self.packages.${system}.container-base;
        };
        
        # flake選択スクリプト
        apps.flake-selector = {
          type = "app";
          program = "${pkgs.writeShellScript "flake-selector" ''
            #!/usr/bin/env bash
            
            echo "=== Single Flake Container Selector ==="
            echo ""
            echo "Available container types:"
            echo "1) Base - Simple container with basic tools"
            echo "2) Node.js - Container with Node.js runtime"
            echo "3) Python - Container with Python runtime"
            echo "4) Go - Container with Go runtime"
            echo "5) Integrated - Container with external flake integration"
            echo ""
            
            read -p "Select container type (1-5): " choice
            
            case $choice in
              1)
                echo "Building base container..."
                nix build .#container-base
                echo "Container built. Load with: podman load < result"
                ;;
              2)
                echo "Building Node.js container..."
                nix build .#container-nodejs
                echo "Container built. Load with: podman load < result"
                ;;
              3)
                echo "Building Python container..."
                nix build .#container-python
                echo "Container built. Load with: podman load < result"
                ;;
              4)
                echo "Building Go container..."
                nix build .#container-go
                echo "Container built. Load with: podman load < result"
                ;;
              5)
                echo "Building integrated container with external flakes..."
                nix build .#container-integrated
                echo "Container built. Load with: podman load < result"
                echo "Run with: podman run --rm localhost/integrated-container:latest [info|test]"
                ;;
              *)
                echo "Invalid selection"
                exit 1
                ;;
            esac
          ''}";
        };
        
        # 開発用シェル（外部パッケージ統合）
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            docker
            skopeo
            dive
            bats
          ] ++
          # external-devshellからのパッケージを安全に収集
          (collectExternalPackages external-devshell system) ++
          # external-orchestraからのパッケージを安全に収集
          (collectExternalPackages external-orchestra system);
          
          shellHook = ''
            echo "Single Flake Multi-Container Development Shell"
            echo ""
            echo "External packages integrated from:"
            echo "  - external-devshell: ${toString (collectExternalPackages external-devshell system)}"
            echo "  - external-orchestra: ${toString (collectExternalPackages external-orchestra system)}"
            echo ""
            echo "Commands:"
            echo "  nix run .#flake-selector         - Interactive container selector"
            echo "  nix build .#container-base        - Build base container"
            echo "  nix build .#container-nodejs      - Build Node.js container"
            echo "  nix build .#container-python      - Build Python container"
            echo "  nix build .#container-go          - Build Go container"
            echo "  nix build .#container-integrated  - Build integrated container"
            echo "  podman load < result              - Load into Podman"
            echo ""
            echo "Testing:"
            echo "  bats test_container.bats            - Test individual containers"
            echo "  bats test_integrated_container.bats - Test integrated container"
            echo "  bats test_external_flake.bats       - Test external flakes"
          '';
        };
      });
}