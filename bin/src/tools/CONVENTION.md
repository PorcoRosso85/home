# ツール開発規約

## 基本方針

1. ツールは単体で動作可能なスクリプトとして実装する
2. 依存関係は必要最小限とし、可能な限りスクリプト内で解決する
3. エラーハンドリングを適切に行い、ユーザーに分かりやすいメッセージを提供する
4. 設定ファイルの操作は安全性を最優先し、必ずバックアップを作成する

## ディレクトリ構造

- `/home/nixos/bin/src/tools`: すべてのツールスクリプトを格納
- `/home/nixos/bin/src/tools/disabled`: 無効化されたツールを格納（ビルド対象外）
- `/home/nixos/bin/src/tools.txt`: ビルド対象のツールリスト

## ファイル名規約

- Bashスクリプト: `*.sh`
- Pythonスクリプト: `*.py`
- JavaScriptスクリプト: `*.js`
- 設定/説明用ファイル: `*.md`, `*.txt`, `*.json`

## コンフィグファイル規約

### MCPサーバー設定

MCPサーバー設定ファイルは以下の構造を持つディレクトリに格納：

```
/home/nixos/.config/claudedesktop/mcp_configs/
├── <server_name>.json
├── <server_name>.json
└── disabled/
    └── <disabled_server>.json
```

各JSONファイルは1つのMCPサーバー設定オブジェクトのみを含む：

```json
{
  "command": "<command>",
  "args": ["<arg1>", "<arg2>", ...],
  "env": {
    "ENV_VAR1": "value1",
    "ENV_VAR2": "value2"
  }
}
```

## ビルド手順

1. ツールの実装が完了したら、`/home/nixos/bin/src/tools.txt` にツール名を追加
2. Argcfileがあるディレクトリ（通常は `/home/nixos/bin/src`）で以下を実行:
   ```bash
   argc build
   ```
   または、argcがインストールされていない場合:
   ```bash
   nix run nixpkgs#argc -- build
   ```
3. ビルド後は問題がないか確認:
   ```bash
   argc check
   ```
   または
   ```bash
   nix run nixpkgs#argc -- check
   ```

## ドキュメント

- 各ツールは適切なヘルプ文書を含む
- Bashスクリプトでは `# @describe` と各パラメータの説明を必ず記述
- JavaScript/Pythonではそれぞれ JSDoc / docstring で詳細な説明を提供
