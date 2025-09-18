{
  description = "Litigation Risk Scanner - 訴訟パターン検出ツール";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    edgartools.url = "path:../../flakes/edgartools";  # 既存のedgartools flakeを使用
  };

  outputs = { self, nixpkgs, flake-utils, edgartools }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # edgartoolsのoverlayを適用
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ edgartools.overlays.${system}.default ];
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Python環境（overlayによるedgartoolsを含む）
            (python311.withPackages (ps: with ps; [
              edgartools  # overlayで提供される
              pandas
              numpy
              scikit-learn
              nltk
              spacy
              transformers
              torch
              ipython
              jupyter
              pytest
            ]))
            
            # TypeScript環境
            bun
            
            # Database
            sqlite
          ];

          shellHook = ''
            echo "🔍 Litigation Risk Scanner (MVP)"
            echo ""
            echo "EdgarTools: ✅ Overlay経由で利用可能"
            echo ""
            echo "Python環境:"
            echo "  python fetch_edgar_simple.py"
            echo "  python store/ddl.py"
            echo "  python store/dml.py"
            echo ""
            echo "TypeScript実行:"
            echo "  bun run main.ts"
            echo ""
            echo "DB: risk.db"
          '';
        };
      });
}