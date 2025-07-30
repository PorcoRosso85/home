{
  description = "graph_docs POC - Dual KuzuDB Query Interface";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
    kuzu-py-flake.url = "path:/home/nixos/bin/src/persistence/kuzu_py";
    tags-in-dir.url = "path:/home/nixos/bin/src/poc/tags_in_dir";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, kuzu-py-flake, tags-in-dir, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # 親flakeからPythonバージョンを継承し、追加パッケージを含めて再構築
        basePython = python-flake.packages.${system}.pythonEnv.python;
        pythonEnv = basePython.withPackages (ps: with ps; [
          pytest
          pytest-asyncio
          kuzu  # nixpkgsのkuzuを使用
        ]);

      in
      {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "graph-docs";
          version = "0.1.0";
          src = ./.;
          
          buildInputs = [ pythonEnv ];
          
          installPhase = ''
            mkdir -p $out/bin
            cp mod.py $out/
            cp main.py $out/bin/graph-docs
            chmod +x $out/bin/graph-docs
            
            # Add shebang and module path
            sed -i '1i#!/usr/bin/env python3' $out/bin/graph-docs
            sed -i '2iimport sys; sys.path.insert(0, "'$out'")' $out/bin/graph-docs
          '';
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];
        };

        apps = rec {
          default = {
            type = "app";
            program = let
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                プロジェクト: graph_docs POC
                
                責務: 2つのKuzuDBディレクトリに対する同時クエリとリレーション定義
                
                利用可能なコマンド:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${./.}
              exec ${pythonEnv}/bin/pytest -v
            ''}";
          };
          
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              cat ${./README.md}
            ''}";
          };

          query = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/graph-docs";
          };

          analyze-code = {
            type = "app";
            program = "${pkgs.writeShellScript "analyze-code" ''
              echo "📊 Analyzing code structure..."
              echo ""
              echo "📁 Current directory: $(pwd)"
              echo ""
              
              # Pythonファイルの統計
              echo "📈 Python files statistics:"
              echo "  Total .py files: $(find . -name "*.py" -type f | grep -v __pycache__ | wc -l)"
              echo ""
              
              # ファイルごとの行数
              echo "📄 Lines of code per file:"
              find . -name "*.py" -type f | grep -v __pycache__ | while read -r file; do
                lines=$(wc -l < "$file")
                echo "  $(basename "$file"): $lines lines"
              done | sort -k2 -nr
              echo ""
              
              # 関数とクラスの簡易カウント
              echo "🔍 Functions and classes:"
              echo "  Functions (def): $(grep -h "^def " *.py 2>/dev/null | wc -l)"
              echo "  Classes (class): $(grep -h "^class " *.py 2>/dev/null | wc -l)"
              echo ""
              
              # インポートの統計
              echo "📦 Import statistics:"
              echo "  Total imports: $(grep -h "^import \|^from " *.py 2>/dev/null | wc -l)"
              echo "  Unique modules: $(grep -h "^import \|^from " *.py 2>/dev/null | awk '{print $2}' | sort -u | wc -l)"
            ''}";
          };

          compare-with = {
            type = "app";
            program = "${pkgs.writeShellScript "compare-with" ''
              if [ -z "$1" ]; then
                echo "Usage: nix run .#compare-with -- /path/to/other/directory"
                exit 1
              fi
              
              OTHER_DIR="$1"
              echo "📊 Comparing code structure between:"
              echo "  📁 Current: $(pwd)"
              echo "  📁 Other: $OTHER_DIR"
              echo ""
              
              # 現在のディレクトリの統計
              echo "1️⃣ Current directory statistics:"
              current_py=$(find . -name "*.py" -type f | grep -v __pycache__ | wc -l)
              current_funcs=$(grep -h "^def " *.py 2>/dev/null | wc -l)
              current_classes=$(grep -h "^class " *.py 2>/dev/null | wc -l)
              echo "  - Python files: $current_py"
              echo "  - Functions: $current_funcs"
              echo "  - Classes: $current_classes"
              echo ""
              
              # 比較対象の統計
              echo "2️⃣ Other directory statistics:"
              other_py=$(find "$OTHER_DIR" -name "*.py" -type f | grep -v __pycache__ | wc -l)
              other_funcs=$(grep -h "^def " "$OTHER_DIR"/*.py 2>/dev/null | wc -l)
              other_classes=$(grep -h "^class " "$OTHER_DIR"/*.py 2>/dev/null | wc -l)
              echo "  - Python files: $other_py"
              echo "  - Functions: $other_funcs"
              echo "  - Classes: $other_classes"
              echo ""
              
              # 共通のファイル名を探す
              echo "🔄 Common file names:"
              comm -12 <(find . -name "*.py" -type f -exec basename {} \; | sort | uniq) \
                       <(find "$OTHER_DIR" -name "*.py" -type f -exec basename {} \; | sort | uniq) | \
              while read -r file; do
                echo "  - $file"
              done
              
              # 共通の関数名を探す（簡易版）
              echo ""
              echo "🔗 Common function names (top 10):"
              comm -12 <(grep -h "^def " *.py 2>/dev/null | sed 's/def \([^(]*\).*/\1/' | sort | uniq) \
                       <(grep -h "^def " "$OTHER_DIR"/*.py 2>/dev/null | sed 's/def \([^(]*\).*/\1/' | sort | uniq) | \
              head -10 | while read -r func; do
                echo "  - $func()"
              done
            ''}";
          };
        };
      }
    );
}