# log - 全言語共通ログAPI規約

## 概要

全言語で統一されたログ出力APIを提供する規約実装モジュール。

## このモジュールの意義

### 1. **言語間の一貫性**
どの言語を使っても同じ形式でログを出力できる統一インターフェース。

```python
# Python
log("INFO", "/api/v1/users/login", "User logged in", user_id="123")

# JavaScript  
log("INFO", "/api/v1/users/login", "User logged in", {userId: "123"})

# Go
Log("INFO", "/api/v1/users/login", "User logged in", map[string]string{"user_id": "123"})

# Shell
log INFO /api/v1/users/login "User logged in" user_id=123
```

### 2. **Unix哲学との調和**
- 標準出力へのシンプルな出力
- パイプラインでの処理を前提
- 他のツールとの組み合わせが容易

### 3. **最小限の規約**
- 呼び出し方法のみを規定
- データ構造は使用者の自由
- 過度な制約を課さない

## 責務（このモジュールがやること）

### 1. **ログ出力API（`log`関数）の提供**
全言語で以下の引数構成を統一：
- 第1引数: ログレベル（文字列）
- 第2引数: URI（文字列） - 発生場所を示すURI/パス
- 第3引数: メッセージ（文字列）
- 第4引数以降: 追加のコンテキスト情報（キーバリュー形式）

#### URIの例
- HTTPエンドポイント: `/api/v1/users/login`
- ファイルパス: `/var/log/app.log` または `file:///etc/config.yaml`
- 内部処理: `internal://auth/validate`
- コマンド: `cmd://git/commit`
- データベース: `db://users/insert`

### 2. **JSONL変換機能（`to_jsonl`関数）の提供**
構造化データをJSONL（JSON Lines）形式に変換する機能：
- 1行1JSONオブジェクト
- 改行区切り
- ストリーム処理に最適

### 3. **各言語での規約準拠実装**
- Python実装
- JavaScript実装
- Go実装
- Shell実装
- （将来）共通バイナリ + 各言語バインディング

## 責務外（このモジュールがやらないこと）

### 1. **ログのデータ構造定義**
- ❌ 必須フィールドの強制
- ❌ スキーマの定義
- ❌ フィールドの型制約

**理由**: 各アプリケーションが自由にログ構造を設計できるようにするため。

### 2. **ログの永続化**
- ❌ ファイルへの書き込み
- ❌ データベースへの保存
- ❌ ログローテーション

**理由**: Unix哲学に従い、永続化は別のツールの責務とする。

### 3. **ログのフィルタリング・加工**
- ❌ ログレベルによるフィルタリング
- ❌ ログの集約・統計
- ❌ ログのフォーマット変換（JSONL以外）

**理由**: これらは後段のツールで処理すべき。

### 4. **エラーハンドリング**
- ❌ ログ出力失敗時のリトライ
- ❌ バッファリング
- ❌ 非同期処理

**理由**: シンプルさを保ち、複雑性を排除。

### 5. **設定管理**
- ❌ ログレベルの設定
- ❌ 出力先の設定
- ❌ フォーマットのカスタマイズ

**理由**: 設定は使用側の責務。

## 設計原則

### 1. **シンプルさ**
最小限のAPIで最大限の互換性を実現。

### 2. **非侵襲的**
アプリケーションの設計に制約を課さない。

### 3. **パイプライン指向**
```bash
app | to_jsonl | gzip > logs.jsonl.gz
app | to_jsonl | jq '.level == "ERROR"'
```

### 4. **言語中立**
特定の言語の慣習に依存しない設計。

## 使用例

### 基本的な使用
```python
from log import log, to_jsonl

# ログ出力
result = log("INFO", "/api/v1/payment/process", "Payment processed", 
            amount=1000, currency="JPY", user_id="user123")

# JSONL変換（必要な場合）
data = {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "test"}
jsonl_line = to_jsonl(data)
```

### パイプラインでの使用
```bash
# アプリケーションのログをJSONL形式で保存
./myapp | python -c "import sys, log; [print(log.to_jsonl(line)) for line in sys.stdin]" > app.jsonl

# エラーログのみ抽出
cat app.jsonl | jq 'select(.level == "ERROR")'
```

## 将来の拡張

### バイナリ実装
高性能な共通実装（C/Rust）を作成し、各言語からバインディング経由で利用：
- メモリ効率の改善
- パフォーマンスの統一
- より多くの言語サポート

### 追加言語サポート
- Ruby
- PHP  
- Java/Kotlin
- Swift
- その他

## まとめ

このモジュールは「どのようにログを出力するか」という**呼び出し規約**のみを提供し、「何を出力するか」は完全に使用者の自由とする。これにより、最大限の柔軟性を保ちながら、言語間の一貫性を実現する。