# 責務: manifest.cue群からcapsules/index.cueを決定的に生成するflake
# MUST: 安定ソート + cue fmt + genVersion/genHash 埋め込み
# MUST: env -i で実行、時刻/乱数未使用

{
  description = "contracts index flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    src.url = "path:../..";  # monorepoルート（manifest群）
  };

  outputs = { self, nixpkgs, src, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in
    {
      packages.${system}.contracts-index = pkgs.stdenv.mkDerivation {
        name = "contracts-index";
        src = src;
        buildInputs = [ pkgs.go pkgs.cue ];

        buildPhase = ''
          # TODO: gate gen-index 実装後に置き換え
          # env -i で決定的実行
          mkdir -p $out
          echo '// 責務: URI→最小辞書（決定的生成；genVersion/genHash埋め込み）' > $out/index.cue
          echo '// MUST: 手編集・コミット禁止' >> $out/index.cue
          echo 'package capsules_index' >> $out/index.cue
          echo '' >> $out/index.cue
          echo 'Caps: {}  // TODO: manifest.cueから生成' >> $out/index.cue
        '';

        installPhase = "true";
      };
    };
}
