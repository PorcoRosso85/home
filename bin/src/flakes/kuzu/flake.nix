{
  description = "Kuzu - Embedded property graph database built for speed";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "kuzu";
          version = "0.9.1"; # バージョンはCMakeListsから取得

          src = pkgs.fetchFromGitHub {
            owner = "kuzudb";
            repo = "kuzu";
            rev = "master"; # 特定のリリースを使用する場合はタグに変更することをお勧めします
            sha256 = "sha256-Ob8zS168SrI3j0tPTxch9I8gHfo86ylMXOLeYQeCpqQ=";
          };

          nativeBuildInputs = with pkgs; [
            cmake
            ninja
            pkg-config
          ];

          buildInputs = with pkgs; [
            # 必要な依存関係
            zlib
            python3
          ];

          cmakeFlags = [
            "-DCMAKE_BUILD_TYPE=Release"
            "-DBUILD_PYTHON=OFF"
            "-DBUILD_JAVA=OFF"
            "-DBUILD_NODEJS=OFF"
            "-DBUILD_RUST=OFF"
            "-DBUILD_BENCHMARKS=OFF"
            "-DBUILD_TESTS=OFF"
          ];

          meta = with pkgs.lib; {
            description = "Embedded property graph database built for speed";
            homepage = "https://github.com/kuzudb/kuzu";
            license = licenses.asl20;
            platforms = platforms.all;
            maintainers = [ ]; # 必要に応じてメンテナを追加
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            cmake
            ninja
            pkg-config
            zlib
            python3
          ] ++ self.packages.${system}.default.nativeBuildInputs
            ++ self.packages.${system}.default.buildInputs;
        };
      });
}
