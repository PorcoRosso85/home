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
        
        # Deno実行環境
        denoEnv = pkgs.deno;
        
        # 開発ツール
        devTools = with pkgs; [
          # TypeScript開発
          nodePackages.typescript
          nodePackages.typescript-language-server
          
          # フォーマッタとリンター
          nodePackages.prettier
          dprint
          
          # テストツール
          nodePackages.vitest
        ];

      in
      {
        # 開発シェル
        devShells.default = pkgs.mkShell {
          buildInputs = [ denoEnv ] ++ devTools;
          
          shellHook = ''
            echo "Claude Graph POC 開発環境"
            echo "========================"
            echo ""
            echo "利用可能なコマンド:"
            echo "  deno test    - テストを実行"
            echo "  deno fmt     - コードフォーマット"
            echo "  deno lint    - リント実行"
            echo "  deno run     - スクリプト実行"
            echo ""
            echo "テスト実行例:"
            echo "  deno test taskExplorer.test.ts"
            echo "  deno test taskPlanner.test.ts"
            echo "  deno test claudeIntegration.test.ts"
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
            set -euo pipefail
            
            echo "🧪 Claude Graph POC テスト実行"
            echo "=============================="
            echo ""
            
            # テストファイルの存在確認
            if [ ! -f "taskExplorer.test.ts" ] || [ ! -f "taskPlanner.test.ts" ] || [ ! -f "claudeIntegration.test.ts" ]; then
              echo "❌ エラー: テストファイルが見つかりません"
              echo "現在のディレクトリ: $(pwd)"
              echo "必要なファイル:"
              echo "  - taskExplorer.test.ts"
              echo "  - taskPlanner.test.ts"
              echo "  - claudeIntegration.test.ts"
              exit 1
            fi
            
            # 各テストを実行
            echo "📋 taskExplorer.test.ts を実行中..."
            ${denoEnv}/bin/deno test taskExplorer.test.ts --allow-read || true
            echo ""
            
            echo "📋 taskPlanner.test.ts を実行中..."
            ${denoEnv}/bin/deno test taskPlanner.test.ts --allow-read || true
            echo ""
            
            echo "📋 claudeIntegration.test.ts を実行中..."
            ${denoEnv}/bin/deno test claudeIntegration.test.ts --allow-read || true
            echo ""
            
            echo "✅ 全てのテストを実行しました"
            echo ""
            echo "📌 注意: 現在はTDD Redフェーズのため、全てのテストが失敗することが期待されています"
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