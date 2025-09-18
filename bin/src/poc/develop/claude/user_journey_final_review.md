# ユーザージャーニー最終レビュー

## 重要な事実
**Claudeの出力は自動的にstream.jsonlに記録される**
→ 明示的なログ処理は不要

## 改訂版フロー

```
[me] ──「認証機能作って」──> [you]
                              │
                              ├─ GraphDB仕様確認
                              │   └─> spec_id: auth_jwt_v2
                              │
                              └─ /org --spec-id auth_jwt_v2
```

### Claude memberの動作（シンプル版）

```
[Claude member]
    │
    ├─ 起動（spec_id受け取り）
    │
    ├─ 思考を出力（自動的にstream.jsonlへ）
    │   "JWT認証実装を開始します。
    │    spec_id: auth_jwt_v2の仕様を確認します。"
    │
    ├─ GraphDBクエリを出力（自動的にstream.jsonlへ）
    │   "実行クエリ:
    │    MATCH (spec:Specification {id: 'auth_jwt_v2'})
    │    RETURN spec.tests, spec.acceptance_criteria"
    │
    ├─ 実装
    │
    └─ エラー時も同様に出力するだけ
        "エラー: trait Clone not implemented
         原因: UserCredentials構造体でClone必要
         解決策をGraphDBから検索します..."
```

## 新たな疑問点

### 1. GraphDBアクセス方法の具体化

```
疑問: memberはどうやってGraphDBにアクセスする？
      
案1: 環境変数でエンドポイント渡す
     GRAPH_ENDPOINT=http://localhost:8080

案2: Claudeの標準ツールとして提供？
     
案3: member/main.sh.templateの関数を使う？
```

### 2. 出力フォーマットの統一

```
疑問: 「背景を出力する」の具体的なフォーマットは？

自由形式？
"なぜかというと..."

構造化？
"=== エラー対応背景 ===
エラー種別: trait_not_implemented
対象: UserCredentials
理由: ..."
```

### 3. GraphDB障害時の動作

```
疑問: GraphDBにアクセスできない時の振る舞いは？

[Claude member]
    │
    ├─ GraphDB接続試行
    │   └─> タイムアウト
    │
    └─ どうする？
        A) エラーで停止
        B) ローカル知識で継続
        C) エスカレーション
```

### 4. 並行実行時の出力混在

```
疑問: 複数memberが同時に出力したら？

[Claude A] ─> "エラー解析中..."
[Claude B] ─> "テスト実行中..."  ← 混在する？
[Claude A] ─> "解決策発見..."

各memberのstream.jsonlは分離されている？
それとも後でmerge？
```

### 5. spec_idが存在しない場合

```
疑問: 渡されたspec_idがGraphDBに無い場合は？

/org --spec-id typo_spec_id  ← タイポ

[Claude member]
    │
    ├─ GraphDB照会
    │   └─> spec not found
    │
    └─ どう振る舞う？
```

## 明確になったこと

✅ graph_context.json は不要
✅ 出力するだけでログになる
✅ memberは自律的にGraphDBアクセス
✅ 背景出力が重要

## まだ不明な点

❓ GraphDBアクセスの具体的実装
❓ エラー時の振る舞い詳細
❓ 出力フォーマットの規約
❓ 並行実行時の調整

これらの疑問を解決する必要がありますか？