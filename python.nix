{ pkgs, ... }:

let
  uv = pkgs.stdenv.mkDerivation {
    pname = "uv";
    version = "0.4.24";  # 適切なバージョンを指定
    src = pkgs.fetchFromGitHub {
      owner = "astral-sh";
      repo = "uv";
      rev = "0.4.24";  # 適切なリビジョンを指定
      sha256 = "";  # 正しいsha256ハッシュ値を指定
    };
    buildInputs = [ pkgs.python3 ];  # Python依存関係
  };
in
with pkgs; [
  # uv
]
