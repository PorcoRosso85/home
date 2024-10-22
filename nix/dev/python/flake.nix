{
  description = "python";

  inputs = {
    # 下記は不要かもしれない, 呼び出し元のflakeから継承されるため
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
  };

  outputs = { self, nixpkgs }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
      uv = pkgs.stdenv.mkDerivation {
        pname = "uv";
        version = "0.4.24";  # 適切なバージョンを指定
        src = pkgs.fetchFromGitHub {
          owner = "astral-sh";
          repo = "uv";
          rev = "0.4.24";  # 適切なリビジョンを指定
          sha256 = "";  # 正しいsha256ハッシュ値を指定
        };
        # buildInputs = [ pkgs.python3 ];  # Python依存関係
      };
    in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python312
          # uv
          pipx
        ];

        shellHook = ''
          echo "##### python by flake #####"
        '';
      };
    };
}
