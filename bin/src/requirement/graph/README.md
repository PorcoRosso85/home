# Requirement Graph Logic (RGL)

LLM専用の要件管理システム。階層ルールを強制し、フィードバックループで学習を促進。

## 使い方（これ以外は使わない）

```bash
echo '{"type": "cypher", "query": "CREATE ..."}' | \
  LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ \
  RGL_DB_PATH=./rgl_db \
  python run.py
```

## 必須環境変数

- `LD_LIBRARY_PATH`: KuzuDB用のライブラリパス
- `RGL_DB_PATH`: データベースファイルのパス

## フィードバックループ

1. **Cypherクエリ送信** → **階層検証**
2. **違反** → **エラー + 負のスコア(-1.0)** → **LLM学習**
3. **修正** → **要件として追加**

## 階層ルール

- Level 0: ビジョン
- Level 1: アーキテクチャ  
- Level 2: モジュール
- Level 3: コンポーネント
- Level 4: タスク

**親は必ず子より上位階層**

## レスポンス形式

```json
{
  "status": "success|error",
  "score": -1.0 ~ 1.0,
  "message": "...",
  "suggestion": "..."
}