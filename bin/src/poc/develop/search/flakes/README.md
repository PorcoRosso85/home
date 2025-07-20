# flake.nix検索ツール

## 責務
指定ディレクトリ配下のflake.nixをfzf探索可能にする

## 使用技術
- fd-find: 高速ファイル検索
- fzf: インタラクティブ選択
- eza: ディレクトリプレビュー

## 実行
```bash
nix run .
```