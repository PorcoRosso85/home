# PDF Analysis POC

## 責務
日本の官報PDFからテキストを抽出し、ログファイルに出力するPOC実装。

## 機能
1. 指定URLからPDFをダウンロード
2. PDFからテキストを抽出（pypdf2使用）
3. 抽出したテキストをlog.txtに出力

## 使用方法
```bash
nix develop
python pdf.py
```

## 出力
- `log.txt`: 抽出したテキスト内容