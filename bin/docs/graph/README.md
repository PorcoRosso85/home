# Flake Responsibility Graph

## 責務
bin/src配下の各flakeの責務を探索可能にし、プロジェクト全体の構造を可視化する。

## 使用方法

### 基本的な使用
```bash
# flake情報の分析と可視化
nix run . -- analyze /home/nixos/bin/src

# キーワード検索
nix run . -- search "ログ"
nix run . -- search "vector" --use-vss  # 意味的類似検索

# 依存関係の確認
nix run . -- deps telemetry/log_py
nix run . -- deps telemetry/log_py --reverse  # 逆引き（誰が使っているか）
```

### データエクスポート
```bash
# 基本的なエクスポート（全flake情報をJSON形式で出力）
nix run . -- export /home/nixos/bin/src

# 言語フィルタ付きエクスポート
nix run . -- export /home/nixos/bin/src --language python
```

## 依存パッケージ例

```nix
{
  inputs = {
    flake-graph.url = "path:./../../docs/graph";
    kuzu_py.url = "path:./../../persistence/kuzu_py";
    log_py.url = "path:./../../telemetry/log_py";
    vss_kuzu.url = "path:./../../search/vss_kuzu";
  };

  outputs = { self, flake-graph, kuzu_py, log_py, vss_kuzu, ... }: {
    # flake-graphの機能を利用
    devShells.x86_64-linux.default = flake-graph.devShell;
    
    # または個別のパッケージを組み合わせて利用
    packages.x86_64-linux.my-analyzer = {
      # KuzuDBでグラフ構造を永続化
      database = kuzu_py.lib.createDB;
      # ログ出力機能
      logger = log_py.packages.x86_64-linux.logger;
      # VSS検索機能
      search = vss_kuzu.lib.vectorSearch;
    };
  };
}
```