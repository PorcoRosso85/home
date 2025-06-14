{
  description = "LightPanda browser (prebuilt binary)";
  
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        
        # システムに応じたバイナリ名
        binaryName = 
          if system == "x86_64-linux" then "lightpanda-x86_64-linux"
          else if system == "aarch64-darwin" then "lightpanda-aarch64-macos"
          else throw "Unsupported system: ${system}";
        
      in {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "lightpanda";
          version = "nightly";
          
          # GitHubのnightly releaseからダウンロード
          src = pkgs.fetchurl {
            url = "https://github.com/lightpanda-io/browser/releases/download/nightly/${binaryName}";
            # ハッシュは実行時に取得されるため、初回は失敗します
            # エラーメッセージに表示される正しいハッシュを設定してください
            hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
          };
          
          # バイナリなのでビルドフェーズは不要
          dontUnpack = true;
          dontBuild = true;
          
          # 依存ライブラリ
          nativeBuildInputs = with pkgs; [ autoPatchelfHook ];
          buildInputs = with pkgs; [ gcc.cc.lib stdenv.cc.cc.lib ];
          
          installPhase = ''
            runHook preInstall
            
            mkdir -p $out/bin
            cp $src $out/bin/lightpanda
            chmod +x $out/bin/lightpanda
            
            runHook postInstall
          '';
          
          meta = with pkgs.lib; {
            description = "The headless browser designed for AI and automation";
            homepage = "https://github.com/lightpanda-io/browser";
            platforms = [ "x86_64-linux" "aarch64-darwin" ];
            mainProgram = "lightpanda";
          };
        };
        
        # 実行可能なアプリケーション
        apps.default = flake-utils.lib.mkApp {
          drv = self.packages.${system}.default;
        };
      });
}