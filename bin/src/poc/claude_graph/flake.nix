{
  description = "Claude Graph POC - KuzuDBによる自律的タスク探索・計画";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # ソースをフィルタリング（.tsファイルとCypherファイルのみ）
        src = pkgs.lib.cleanSourceWith {
          src = ./.;
          filter = path: type:
            let baseName = baseNameOf path;
            in pkgs.lib.hasSuffix ".ts" baseName ||
               pkgs.lib.hasSuffix ".cypher" baseName ||
               pkgs.lib.hasSuffix ".md" baseName ||
               pkgs.lib.hasSuffix ".json" baseName ||
               pkgs.lib.hasSuffix ".nix" baseName ||
               type == "directory";
        };
        
        # Deno実行環境
        denoEnv = pkgs.deno;
        
        # Python環境
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          pytest
          hypothesis
          pytest-snapshot
        ]);
        
        # 開発ツール
        devTools = with pkgs; [
          # TypeScript開発
          nodePackages.typescript
          nodePackages.typescript-language-server
          
          # フォーマッタとリンター
          nodePackages.prettier
          dprint
          
        ];

      in
      {
        # 開発シェル
        devShells.default = pkgs.mkShell {
          buildInputs = [ denoEnv pythonEnv ] ++ devTools;
          
          shellHook = ''
            echo "Claude Graph POC 開発環境"
            echo "========================"
            echo ""
            echo "利用可能なコマンド:"
            echo ""
            echo "Deno (単体テスト):"
            echo "  deno test    - テストを実行"
            echo "  deno fmt     - コードフォーマット"
            echo "  deno lint    - リント実行"
            echo "  deno run     - スクリプト実行"
            echo ""
            echo "Python (E2Eテスト):"
            echo "  pytest       - E2Eテストを実行"
            echo "  pytest -v    - 詳細なテスト結果を表示"
            echo "  pytest --snapshot-update - スナップショットを更新"
            echo ""
            echo "テスト実行例:"
            echo "  deno test taskExplorer.test.ts"
            echo "  pytest test_e2e.py"
            echo "  pytest test_e2e.py::test_specific_case"
            echo ""
            echo "規約チェック:"
            echo "  - レイヤー分離を確認"
            echo "  - Result型によるエラーハンドリング"
            echo "  - 純粋関数の使用"
            echo ""
          '';
        };
        
        # テスト実行スクリプト
        apps.test = {
          type = "app";
          program = toString (pkgs.writeShellScript "run-tests" ''
            #!/usr/bin/env bash
            echo "🧪 Claude Graph POC テストを実行するには、以下のコマンドを使用してください:"
            echo ""
            echo "  cd ${placeholder "out"}"
            echo "  nix develop -c deno test . --allow-read --no-check --filter=\"/(taskExplorer|taskPlanner|versionBasedExplorer)/\""
            echo ""
            echo "または:"
            echo ""
            echo "  cd ${placeholder "out"}"
            echo "  nix develop -c ./run-tests.sh"
          '');
        };
        
        # フォーマット実行スクリプト
        apps.format = {
          type = "app";
          program = toString (pkgs.writeShellScript "format-code" ''
            #!/usr/bin/env bash
            set -euo pipefail
            
            echo "🎨 コードフォーマット実行"
            echo "======================="
            
            ${denoEnv}/bin/deno fmt *.ts
            
            echo "✅ フォーマット完了"
          '');
        };
        
        # 規約チェックスクリプト
        apps.check-conventions = {
          type = "app";
          program = toString (pkgs.writeShellScript "check-conventions" ''
            #!/usr/bin/env bash
            set -euo pipefail
            
            echo "📏 規約準拠チェック"
            echo "=================="
            echo ""
            
            # テストファイルの規約チェック
            echo "🔍 テストファイルの規約チェック..."
            
            # Result型の使用確認
            echo -n "  Result型の使用: "
            if grep -q "type.*Result.*=.*{.*ok:.*true.*}.*{.*ok:.*false.*}" *.test.ts; then
              echo "✅"
            else
              echo "❌ Result型が定義されていません"
            fi
            
            # 純粋関数の確認
            echo -n "  純粋関数の定義: "
            if grep -q "declare function" *.test.ts; then
              echo "✅"
            else
              echo "❌ 純粋関数が定義されていません"
            fi
            
            # 高階関数の確認
            echo -n "  高階関数パターン: "
            if grep -q "create.*function.*(" *.test.ts; then
              echo "✅"
            else
              echo "❌ 高階関数パターンが使用されていません"
            fi
            
            echo ""
            echo "📝 推奨事項:"
            echo "  - レイヤー分離（Domain/Application/Infrastructure）"
            echo "  - エラーを値として返す（例外を投げない）"
            echo "  - 依存性注入による疎結合化"
            echo "  - テストファーストの実践"
          '');
        };
        
        # パッケージ定義
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "claude-graph-poc";
          version = "0.1.0";
          
          src = ./.;
          
          buildInputs = [ denoEnv ];
          
          installPhase = ''
            mkdir -p $out/bin
            cp -r * $out/
            
            # 実行スクリプトの作成
            cat > $out/bin/claude-graph-poc <<EOF
            #!/usr/bin/env bash
            cd $out
            ${denoEnv}/bin/deno run --allow-read --allow-net example.ts
            EOF
            chmod +x $out/bin/claude-graph-poc
          '';
          
          meta = with pkgs.lib; {
            description = "ClaudeがKuzuDBを使って自律的にタスクを探索・計画するPOC";
            license = licenses.mit;
            platforms = platforms.all;
          };
        };
      });
}