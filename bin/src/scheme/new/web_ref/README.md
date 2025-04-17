# 機能追加検討ディレクトリ

このディレクトリは「機能追加を検討されているシングルファイル機能もしくは既存実装への依存する機能」を格納するためのものです。

## Shebang情報

当プロジェクトのファイルでは以下のShebangを使用しています：

```
#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run
```

この設定により、nixパッケージマネージャ経由でDenoを使用して実行できます。実行時には、読み取り・書き込み・他プログラム実行の権限が付与されます。
