# log - 全言語共通ログAPI規約

標準出力への統一ログAPI。`log = stdout`。

## API

```
log(level, data) → stdout
```

- **level**: 文字列（"INFO", "ERROR", "METRIC"等、自由定義）
- **data**: 辞書型（必須: uri, message）

## 責務

1. **2引数API** - `log(level, data)`
2. **JSONL出力** - 1行1JSON
3. **stdout出力** - 他の出力先は責務外
4. **型拡張可能** - dataは自由に拡張

## 責務外

- スキーマ定義
- 永続化・ローテーション
- フィルタリング・集約
- エラーハンドリング
- 設定管理

## 設計原則

1. **シンプル** - 最小限API
2. **非侵襲的** - 制約なし
3. **パイプライン指向** - Unixフィロソフィ準拠
4. **言語中立** - 慣習に依存しない
5. **拡張可能** - 型による暗黙的フォーマット

## 基本使用例

```
# 各言語での呼び出し
log("INFO", {uri: "/api/users", message: "User created", userId: "123"})

# 出力（JSONL）
{"level":"INFO","uri":"/api/users","message":"User created","userId":"123"}
```

## 型拡張

必須フィールド（uri, message）を含む限り、自由に拡張可能：

```
# アプリケーション固有フィールド追加
log("METRIC", {
    uri: "/api/health",
    message: "Health check",
    requestId: "req-123",    # 拡張
    latencyMs: 42            # 拡張
})
```

## パイプライン統合

```bash
# ログフィルタリング
app | jq 'select(.level == "ERROR")'

# 外部システム連携
app | logger -t app
app | to_syslog
app | to_cloudwatch
```

## 実装構造

### モジュール構成（DDD）

```
log/
├── domain/          # ビジネスロジック・型定義
├── application/     # API実装・ユースケース
├── infrastructure/  # 出力実装（stdout）
└── __init__.py等    # 公開API
```

### 各層の責務

**Domain層**
- ログレベル・データ型の定義
- ビジネスルールの表現
- 言語固有の型システム活用

**Application層**
- `log(level, data)` APIの実装
- Domain型の検証・変換
- Infrastructure層への委譲

**Infrastructure層**
- stdout への JSONL 出力
- シリアライゼーション
- 出力の技術的詳細

### 実装言語

各言語で同一の振る舞いを実装：
- Python: `__init__.py`
- TypeScript: `mod.ts`
- Go: `log.go`
- Shell: `log.sh`

## まとめ

`log(level, data) → stdout` という単一の約束。
Unixパイプラインとの完全な互換性を保ちながら、
全言語で一貫したログ出力を実現。