{
  description = "Qwen-Code CLI with cached npm package";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          # シンプルなnpmxアプローチ
          qwen-code-npx = pkgs.writeShellScriptBin "qwen-code" ''
            export PATH="${pkgs.nodejs_20}/bin:$PATH"
            exec npx @qwen-code/qwen-code@latest "$@"
          '';

          # ローカルキャッシュアプローチ
          qwen-code-cached = pkgs.writeShellScriptBin "qwen-code" ''
            export PATH="${pkgs.nodejs_20}/bin:$PATH"
            CACHE_DIR="$HOME/.cache/qwen-code-nix"
            
            if [ ! -d "$CACHE_DIR/node_modules" ]; then
              echo "Installing qwen-code to cache..."
              mkdir -p "$CACHE_DIR"
              cd "$CACHE_DIR"
              npm install @qwen-code/qwen-code@latest
            fi
            
            cd "$CACHE_DIR"
            exec ./node_modules/.bin/qwen-code "$@"
          '';
        });

      # 直接実行可能なアプリケーション
      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.qwen-code-cached}/bin/qwen-code";
        };
      });
    };
}