# CLI化の実現方法

## 認識の整理

MCPサーバーもCLIも本質的に同じ：
- **入力**: JSON形式のパラメータ
- **処理**: LSPツール関数の実行
- **出力**: JSON形式の結果

違いは入出力のインターフェースだけ。

## 実装アプローチ

### LSMCPのツール関数を直接呼び出すCLIラッパー

```typescript
// 擬似コード
import { findReferencesWithLSP } from './lsp/tools/lspFindReferences.ts';

// CLIエントリーポイント
async function cli() {
  const args = process.argv.slice(2);
  const command = args[0];
  const params = JSON.parse(args[1]);
  
  switch (command) {
    case 'find-references':
      const result = await findReferencesWithLSP(params);
      console.log(JSON.stringify(result));
      break;
    // 他のコマンド...
  }
}
```

### Nix Flakeでの実装案

```nix
lsmcpCli = pkgs.writeShellScriptBin "lsmcp-cli" ''
  # LSPサーバーを起動
  ${pkgs.pyright}/bin/pyright --languageserver --stdio &
  LSP_PID=$!
  
  # ツール関数を直接実行するNode.jsスクリプト
  node -e "
    // LSPクライアントを初期化
    // ツール関数を実行
    // 結果を出力
  "
  
  kill $LSP_PID
'';
```

## 具体的な実装手順

1. **LSMCPのツール関数を抽出**
   - `lspFindReferences.ts`の`findReferencesWithLSP`
   - `lspRenameSymbol.ts`の`renameSymbolWithLSP`
   - など

2. **CLIインターフェースを作成**
   ```bash
   lsmcp-cli find-references --file main.py --line 10 --symbol Calculator
   lsmcp-cli rename-symbol --old Calculator --new ComputeEngine --pattern "**/*.py"
   ```

3. **LSPサーバーの管理**
   - 起動、初期化、終了を自動化
   - または既存のLSPサーバープロセスを利用

## 利点

- MCPサーバーの起動不要
- バッチ処理が容易
- パイプラインでの使用が可能
- 既存のLSMCPコードを最大限活用