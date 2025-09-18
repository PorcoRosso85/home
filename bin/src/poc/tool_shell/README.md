# Tool Shell POC

自己記述的なツールとNushellの連携パターンを実証する最小限のPOC。

## 構成

```
tool_shell/
├── README.md
├── caller/
│   └── universal.nu        # 汎用的なツール実行スクリプト
└── callee/
    ├── flake.nix           # Nixパッケージ定義
    └── analyzer.exs        # --readme, --test対応のElixirアプリ
```

## 使い方

```bash
# callee側：アプリの動作確認
cd callee
nix run . -- --readme
echo "id,value\n1,150\n2,50" | nix run . -- --threshold 100
nix run . -- --test

# caller側：Nushellから呼び出し
cd caller
nu universal.nu readme ../callee
nu universal.nu test ../callee
echo "id,value\n1,150\n2,50" | nu universal.nu pipe ../callee --threshold 100
```

## ワンライナー例

```nu
# 最もシンプルな使い方
nix run .#analyzer -- --readme
echo "id,value\n1,150" | nix run .#analyzer -- --threshold 100
```