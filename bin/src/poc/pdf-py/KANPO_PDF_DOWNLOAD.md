# 官報PDFダウンロード手順

## URLパターン規則

官報のPDFは以下のURLパターンに従います：

- **HTML URL（iframe埋め込みページ）**: 
  ```
  https://www.kanpo.go.jp/YYYYMMDD/YYYYMMDDhXXXXX/YYYYMMDDhXXXXXnnnnf.html
  ```

- **PDF URL（直接アクセス）**: 
  ```
  https://www.kanpo.go.jp/YYYYMMDD/YYYYMMDDhXXXXX/pdf/YYYYMMDDhXXXXXnnnn.pdf
  ```

### 変換規則
1. 末尾の`f.html`を削除
2. ファイル名の前に`pdf/`ディレクトリを挿入
3. 末尾に`.pdf`を追加

### パラメータ説明
- `YYYYMMDD`: 発行日（例: 20250903）
- `hXXXXX`: 号数（例: h01541）
- `nnnn`: ページ範囲（例: full00010032）

## 実証済みダウンロード例

### 令和7年9月3日 本紙第1541号 全32ページ

```bash
# HTML URL（元のページ）
HTML_URL="https://www.kanpo.go.jp/20250903/20250903h01541/20250903h01541full00010032f.html"

# PDF URLへの変換
PDF_URL=$(echo "$HTML_URL" | sed 's|/\([^/]*\)f\.html$|/pdf/\1.pdf|')

# curlでダウンロード
curl -L -o "kanpo_20250903_h01541_full.pdf" \
     -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
     "$PDF_URL"

# ファイルサイズ確認
ls -lh kanpo_20250903_h01541_full.pdf
# 結果: 4.4MB
```

### ダウンロード成功確認済みのPDF
- **ファイル名**: kanpo_20250903_h01541_full.pdf
- **サイズ**: 4.4MB
- **ページ数**: 32ページ
- **内容**: 令和7年9月3日発行の官報本紙第1541号

## 責務分離

### このディレクトリの責務
- **PDFのダウンロードと保存のみ**
- URLパターンの変換ロジック
- curlコマンドによるファイル取得

### 対象外の責務
- PDF内容の解析（別モジュールで実施）
- OCR処理（pdf_extractor.py等で実施）
- テキスト抽出（専用ツールで実施）

## 実行環境

### 必要なツール
- `curl`: HTTPダウンロード用
- `sed`: URL変換処理用（オプション）

### Nix環境での実行
```bash
# flake.nixが提供する環境で実行
nix develop -c bash -c '
  HTML_URL="https://www.kanpo.go.jp/20250903/20250903h01541/20250903h01541full00010032f.html"
  PDF_URL="${HTML_URL/f.html/.pdf}"
  PDF_URL="${PDF_URL/\/20250903h01541full00010032/\/pdf\/20250903h01541full00010032}"
  curl -L -o "test_download.pdf" \
       -H "User-Agent: Mozilla/5.0" \
       "$PDF_URL"
  echo "Downloaded: $(ls -lh test_download.pdf 2>/dev/null | awk \"{print \$5}\")"
'
```

## 注意事項

1. **User-Agentヘッダー必須**: 一部のサーバーはUser-Agentなしのリクエストを拒否
2. **リダイレクト対応**: `-L`オプションでリダイレクトに追従
3. **エラーハンドリング**: ダウンロード失敗時の再試行ロジックは実装者の判断に委ねる