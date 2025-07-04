# Nu-based Symbol Search Tool

Nushellを使用した最小構成のシンボル検索ツール

## 使用方法

```bash
# Python ファイルのシンボル一覧を取得
nu symbols.nu /path/to/directory --ext py

# JSON形式で出力
nu -c "source symbols.nu; symbols /path/to/directory | to json"
```

## 動作例

```bash
❯ nu ./nu_ctags/symbols.nu ./kuzu_query_logger/ --ext py
```

出力：
- 62個のシンボルを検出
- タイプ別: class(8), function(33), method(21)
- 各シンボルには file, line, type, name が含まれる

## ctagsを使った方が良いケース

### ctagsの利点
1. **高速性**: C言語実装で大規模プロジェクトでも高速
2. **言語サポート**: 50以上の言語に対応
3. **高度な解析**: 言語固有の複雑な構文を正確に解析
4. **エディタ統合**: vim, emacs等との深い統合
5. **インデックス形式**: 標準的なtagsファイル形式

### 推奨使用場面
- **大規模プロジェクト** (10万行以上のコード)
- **多言語プロジェクト** (C/C++, Java, Go等の混在)
- **CI/CD環境** (高速なインデックス生成が必要)
- **複雑な構文** (マクロ、テンプレート、デコレータ等)
- **既存ツールとの連携** (IDEやエディタプラグイン)

### Nuスクリプトの利点
- 追加インストール不要
- カスタマイズが容易
- 構造化データ処理が得意
- パイプライン処理で柔軟なフィルタリング
- 小〜中規模プロジェクトに最適