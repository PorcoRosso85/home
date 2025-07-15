# 埋め込みモデル アーキテクチャ設計

## 概要
bin/docs/conventionsに従った3層アーキテクチャで埋め込みモデルを抽象化。
モデルの切り替えが容易で、将来的な拡張に対応。

## ディレクトリ構造
```
embeddings/
├── domain/           # ビジネスルールとデータ構造
│   ├── types.py     # 型定義（Protocol, Dataclass）
│   └── __init__.py
├── application/      # ユースケース
│   ├── use_cases.py # テキスト埋め込みサービス
│   └── __init__.py
└── infrastructure/   # 具体的な実装
    ├── ruri_model.py    # Ruri v3実装（30M, 軽量）
    ├── plamo_model.py   # PLaMo実装（1B, 要高メモリ）※コメント化
    ├── factory.py       # モデル生成ファクトリー
    └── __init__.py
```

## 依存関係
```
Infrastructure → Application → Domain
```

## 特徴
1. **プロトコルベース**: `EmbeddingModel` Protocolで抽象化
2. **型安全**: すべての入出力をDataclassで定義
3. **プラグイン対応**: 新しいモデルの追加が容易
4. **メモリ考慮**: 環境に応じたモデル選択が可能

## 使用例
```python
# 軽量モデル（30M parameters）
model = create_embedding_model("ruri-v3-30m")
service = TextEmbeddingService(model)

# 高精度モデル（1B parameters）※要8GB以上メモリ
# model = create_embedding_model("plamo-embedding-1b")
```

## Ruri v3の特徴
- **プレフィックス方式**: 用途に応じた4種類のプレフィックス
  - `""`: セマンティック埋め込み
  - `"トピック: "`: 分類・クラスタリング
  - `"検索クエリ: "`: 検索クエリ用
  - `"検索文書: "`: 検索対象文書用
- **軽量**: 30Mパラメータで低メモリ環境でも動作
- **高速**: Flash Attention 2対応（GPU環境）