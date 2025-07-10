# PLaMo-Embedding-1B + KuzuDB Vector Search POC

## 概要
PLaMo-Embedding-1B（日本語特化埋め込みモデル）とKuzuDB（グラフデータベース）のベクター拡張機能を組み合わせた、日本語セマンティック検索のPOCです。

## 実装内容
- PLaMo-Embedding-1Bによる日本語テキストの埋め込みベクトル生成
- KuzuDBへのベクトルデータ保存とインデックス作成
- 類似度検索の実行

## 実行方法
```bash
# Nix環境での実行
cd bin/src/poc/search/vss_plamo
nix run .#run
```

## 必要な環境
- Nix (flake有効)
- インターネット接続（初回モデルダウンロード時）

## 特徴
- sentence_transformerの代替としてPLaMo-Embedding-1Bを使用
- ローカル環境で完結（データ外部送信なし）
- 日本語に最適化された埋め込み表現