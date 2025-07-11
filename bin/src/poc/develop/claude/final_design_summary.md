# 最終設計まとめ

## 確定事項

### 1. GraphDBアクセス
- **DB URIが環境変数で与えられる**
- memberは直接GraphDBにアクセス可能

### 2. 出力形式
- **出力仕様なし（自由形式）**
- Claudeが自然に背景を説明すればよい

### 3. エラーハンドリング
- **将来追加予定**
- 現時点では考慮不要

### 4. stream.jsonl
- **仕様は一切気にしない**
- Claudeの出力が自動的に記録される
- merge等の処理は考慮不要

### 5. spec_id
- **spec_idという概念は除外**
- GraphDBへの直接クエリで必要な情報を取得

## シンプル化されたフロー

```
[me] ──「認証機能作って」──> [you]
                              │
                              └─ /org auth-impl src/auth "JWT認証実装"
                                      │
                                      ▼
                              [org system]
                                      │
                                      ├─ worktree作成
                                      ├─ DB_URI環境変数セット
                                      └─ member起動
                                            │
                                            ▼
                                    [Claude member]
                                            │
                                            ├─ 「JWT認証を実装します」
                                            ├─ 「必要な仕様をGraphDBから確認」
                                            ├─ 「エラー: Cloneトレイト未実装」
                                            ├─ 「GraphDBに解決策を問い合わせ」
                                            └─ 「#[derive(Clone)]を追加で解決」
```

## 実装に必要な変更

### 1. CLAUDE.md
```
## エラー対応規則
- エラー発生時は、なぜそのエラーが起きたか背景を説明する
- GraphDBへの問い合わせ時は、何を調べるか理由を述べる
- 解決策適用時は、なぜその解決策を選んだか説明する
```

### 2. org/main.sh.template
```bash
# graph_context.json作成部分を削除
# DB_URI環境変数を追加
export DB_URI="${GRAPH_ENDPOINT:-http://localhost:8080/graphql}"
```

### 3. member/main.sh.template
```bash
# エラー時の背景説明付きクエリ例
echo "エラー背景: Cloneトレイトが必要な理由は..."
echo "GraphDBに以下のクエリで問い合わせます:"
echo "MATCH (e:Error {type: 'trait_not_implemented'})..."
```

## 除外された概念

- ❌ spec_id
- ❌ graph_context.json
- ❌ 出力フォーマット仕様
- ❌ stream.jsonl操作
- ❌ エラーハンドリング詳細

これにより、システムは大幅にシンプルになりました。