# KuzuDB Migration POC スタートガイド

## 🎯 このPOCの目的
`architecture/`で設計したKuzuDBマイグレーション戦略を実際に検証します。

## 📋 引継ぎ内容

### 1. 重要な発見
- KuzuDBには`EXPORT DATABASE`/`IMPORT DATABASE`というネイティブ機能がある
- これを使えば完全なマイグレーションが可能

### 2. 提案されたワークフロー
```
開発 → EXPORT → バージョン管理 → IMPORT → デプロイ
```

### 3. 検証すべきこと
- [ ] 本当に動くか？
- [ ] パフォーマンスは？
- [ ] エラー時の対処は？

## 🚀 最初にやること

```bash
# 1. architectureから必要なファイルをコピー
cp ~/bin/src/architecture/infrastructure/*.py ./
cp ~/bin/src/architecture/MIGRATION_*.md ./
cp -r ~/bin/src/architecture/docs ./

# 2. テスト環境を準備
mkdir -p test_db examples results

# 3. 簡単なテストから開始
echo "最初は小さなスキーマでEXPORT/IMPORTを試してみましょう"
```

## 📁 推奨ディレクトリ構造

```
kuzu_migration/
├── START_HERE.md         # このファイル
├── test_simple.py        # 最初に作るテストスクリプト
├── schema_manager.py     # architectureからコピー
├── migration_tool.py     # architectureからコピー
└── results/
    └── test_01_basic.md  # テスト結果を記録
```

## ✅ チェックリスト

### Step 1: 基本動作確認（1日目）
- [ ] KuzuDBでテストDBを作成
- [ ] 簡単なスキーマを定義
- [ ] EXPORT DATABASEを実行
- [ ] 生成されたファイルを確認
- [ ] 別のDBにIMPORT DATABASE

### Step 2: 実践的な検証（2-3日目）
- [ ] requirement/graphのスキーマで試す
- [ ] データを含めた移行
- [ ] バージョン間の移行

### Step 3: ツール開発（4-5日目）
- [ ] migration_tool.pyを実装
- [ ] 自動化スクリプト作成
- [ ] エラーハンドリング追加

## 💡 ヒント

1. **まず手動で試す**: スクリプト化の前に手動でコマンドを実行
2. **小さく始める**: 1つのテーブルから始めて徐々に複雑に
3. **記録を残す**: すべての実行結果を`results/`に保存

## 🔗 参考資料

- architectureでの設計: `~/bin/src/architecture/HANDOVER_TO_POC.md`
- KuzuDB公式ドキュメント: `./docs/2025-08-03_18-12-06_kuzudb.com_migrate.md`

## 📞 質問・相談

設計について不明な点があれば、architectureチームに確認してください。

---
頑張ってください！このPOCの結果が、今後のKuzuDB運用の基盤になります。