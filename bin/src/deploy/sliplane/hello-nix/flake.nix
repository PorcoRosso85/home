# ===== FLAKE.NIX RESPONSIBILITY & FEATURES =====
# 責務: NixOS最小構成コンテナのパッケージ・アプリケーション・開発環境定義
# 提供機能:
#   - packages.default: hello実行バイナリ
#   - apps.default: helloコマンド実行
#   - apps.server: ポート8080のHTTPサーバー(netcat使用)
#   - devShells.default: 開発用シェル環境
#   - packages.dockerImage: Docker用イメージ(将来拡張用)
# 依存:
#   - nixpkgs (NixOS公式パッケージ群)
#   - flake-utils (マルチシステム対応)
# 相互関係:
#   - Dockerfileがserverアプリを実行
#   - README.mdが使用方法を説明
#   - test.shが動作確認を実施
# ===================================================

{
  description = "Minimal NixOS container with hello";

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
        # デフォルトパッケージ
        packages.default = pkgs.hello;

        # アプリケーション定義
        apps.default = {
          type = "app";
          program = "${pkgs.hello}/bin/hello";
        };

        # HTTPサーバー付きアプリケーション
        apps.server = {
          type = "app";
          program = toString (pkgs.writeShellScript "hello-server" ''
            echo "=== Starting NixOS minimal container ==="
            echo "Running hello:"
            ${pkgs.hello}/bin/hello
            echo ""
            echo "=== Starting HTTP server on port 8080 ==="
            
            # Pythonの簡易HTTPサーバーを使用
            ${pkgs.python3}/bin/python3 -c "
import http.server
import socketserver
import subprocess

class HelloHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        result = subprocess.run(['${pkgs.hello}/bin/hello'], capture_output=True, text=True)
        response = f'Hello from Nix flake! {result.stdout.strip()}'
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        print(f'{self.address_string()} - {format % args}')

with socketserver.TCPServer((\"\", 8080), HelloHandler) as httpd:
    print('Server running at http://localhost:8080/')
    httpd.serve_forever()
"
          '');
        };

        # 開発シェル
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            hello
            netcat
            curl
          ];
          
          shellHook = ''
            echo "NixOS minimal development environment"
            echo "Available commands:"
            echo "  nix run          - Run hello"
            echo "  nix run .#server - Run HTTP server"
            echo ""
          '';
        };

        # Dockerイメージ（将来の拡張用）
        packages.dockerImage = pkgs.dockerTools.buildImage {
          name = "hello-nix";
          tag = "latest";
          
          copyToRoot = pkgs.buildEnv {
            name = "image-root";
            paths = with pkgs; [
              hello
              python3
              bashInteractive
              coreutils
            ];
            pathsToLink = [ "/bin" ];
          };

          config = {
            Cmd = [ "${self.apps.${system}.server.program}" ];
            ExposedPorts = {
              "8080/tcp" = {};
            };
          };
        };
      });
}