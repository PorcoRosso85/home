# 環境設定ガイド

## 必須環境変数

### LD_LIBRARY_PATH (Linux/NixOS)

DuckDBやKuzuDBなどのネイティブライブラリを使用する際、`libstdc++.so.6`が必要です。

#### 設定方法

1. **一時的な設定（テスト実行時）**:
   ```bash
   export LD_LIBRARY_PATH=/nix/store/4gk773fqcsv4fh2rfkhs9bgfih86fdq8-gcc-13.3.0-lib/lib:$LD_LIBRARY_PATH
   uv run pytest
   ```

2. **setup_test_env.sh使用（推奨）**:
   ```bash
   ./setup_test_env.sh telemetry/
   ```

3. **永続的な設定（.bashrcまたは.zshrc）**:
   ```bash
   # NixOSでgcc libstdc++を自動検出
   LIBSTDCXX_PATH=$(nix-shell -p gcc --run "find /nix/store -name 'libstdc++.so.6' 2>/dev/null | head -1" 2>/dev/null)
   if [ -n "$LIBSTDCXX_PATH" ]; then
       export LD_LIBRARY_PATH="$(dirname $LIBSTDCXX_PATH):$LD_LIBRARY_PATH"
   fi
   ```

## トラブルシューティング

### "libstdc++.so.6: cannot open shared object file"

このエラーが発生した場合：

1. gcc環境の確認:
   ```bash
   nix-shell -p gcc --run "find /nix/store -name 'libstdc++.so.6'"
   ```

2. 見つかったパスをLD_LIBRARY_PATHに追加

3. それでも解決しない場合は、nixパッケージを更新:
   ```bash
   nix-channel --update
   nix-env -u
   ```

## 依存ライブラリ

| ライブラリ | 用途 | 環境変数要否 |
|-----------|------|-------------|
| SQLite | 組み込みDB | 不要 |
| DuckDB | 分析用DB | 要LD_LIBRARY_PATH |
| KuzuDB | グラフDB | 要LD_LIBRARY_PATH |

## CI/CD設定

GitHub ActionsやGitLab CIでは以下を設定：

```yaml
env:
  LD_LIBRARY_PATH: /usr/lib/x86_64-linux-gnu
```