# Contract-based E2E Testing Framework Specification

## 概要

JSON Schemaを用いた契約ベースのEnd-to-End（E2E）テストフレームワーク。
言語非依存で、任意の実行可能ファイルに対してプロパティベーステストを実行する。

## 設計原則

### Refactoring Wall原則
「実装コードが壁の向こうにあり完全に見えなくても、このテストを書けるか？」
- 実装詳細ではなく、観測可能な振る舞いのみをテスト
- 公開APIとJSON入出力の契約のみに依存

### レイヤードアーキテクチャでの位置づけ
E2Eテストフレームワークは**Infrastructureレイヤー**に属する：
- システム境界をテストする責務
- 外部システムとの契約を検証
- 実プロセスを使用した統合テスト

## アーキテクチャ

### 呼び出し関係

```
your-project/flake.nix
    ↓ (inputs.contract-e2e)
contract_e2e/flake.nix  
    ↓ (subprocess.run)
your-project executable
```

### 責務分離

- **利用側プロジェクト**: 実装とスキーマ定義を提供
- **contract_e2e**: テスト実行エンジンとスキーマ検証を提供

## 動作原理

### 1. スキーマ定義

利用側プロジェクトは以下のスキーマファイルを提供：

```
project/
├── schema/
│   ├── input.schema.json   # 入力形式の定義
│   └── output.schema.json  # 出力形式の定義
```

### 2. テスト実行フロー

1. **初期化時**
   - input/output schemaファイルを読み込み
   - スキーマの妥当性を検証
   - hypothesisの戦略を構築

2. **各テストケース実行時**
   - hypothesisがinput schemaから自動的にテストデータを生成
   - subprocessで対象実行可能ファイルを起動（`nix run`経由）
   - 標準入力にJSONデータを送信
   - 標準出力からJSONレスポンスを取得
   - output schemaで出力を検証

3. **網羅的テスト**
   - デフォルトで100回以上の異なるケースを自動実行
   - エッジケースを含む多様な入力パターンを生成

## 実装要件

### 利用側プロジェクトの要件

1. **実行可能ファイル**
   - stdin/stdoutでJSON入出力に対応
   - エラー時も適切なJSONレスポンスを返す
   - プロセス終了コードの適切な設定（成功:0、失敗:非0）

2. **flake.nix設定**
   ```nix
   {
     inputs.contract-e2e.url = "github:org/contract_e2e";
     
     outputs = { self, contract-e2e, ... }: {
       apps.test.e2e = contract-e2e.lib.mkContractE2ETest {
         executable = self.packages.default;
         inputSchema = ./schema/input.schema.json;
         outputSchema = ./schema/output.schema.json;
       };
     };
   }
   ```

### contract_e2eフレームワークの提供機能

1. **mkContractE2ETest関数**
   - 実行可能ファイルのパスとスキーマを受け取る
   - pytestベースのテストランナーを返す
   - 戻り値の型定義：
   ```typescript
   type TestResult = 
     | { ok: true; report: TestReport }
     | { ok: false; error: TestError };
   ```

2. **テストランナー実装**
   ```python
   class ContractE2ETester:
       def __init__(self, input_schema_path, output_schema_path):
           self.input_schema = json.load(open(input_schema_path))
           self.output_schema = json.load(open(output_schema_path))
       
       def run_tests(self, executable_cmd):
           @given(st.from_schema(self.input_schema))
           def test_contract(input_data):
               result = subprocess.run(
                   ["nix", "run", executable_cmd],
                   input=json.dumps(input_data),
                   capture_output=True,
                   text=True
               )
               output = json.loads(result.stdout)
               jsonschema.validate(output, self.output_schema)
   ```

3. **エラーレポート**
   - スキーマ違反の詳細
   - 失敗したテストケースの入力データ
   - プロセスのstderr出力

## 利点

1. **真のE2Eテスト**
   - プロセス境界を越えた完全なブラックボックステスト
   - 実際のユーザー使用と同じ実行方法

2. **言語非依存**
   - JSON入出力に対応すれば任意の言語で実装可能
   - 統一的なテストアプローチ

3. **自動テスト生成**
   - 手動でテストケースを書く必要なし
   - スキーマから網羅的なケースを自動生成

4. **Nixの再現性**
   - 環境差異によるテスト結果の揺れがない
   - CIでも開発環境と同一の結果

## 制約事項

1. **パフォーマンス**
   - 各テストケースでプロセス起動のオーバーヘッド
   - 大量のテストケース実行には時間がかかる

2. **ステートフルアプリケーション**
   - 状態を持つアプリケーションのテストには工夫が必要
   - 各テストケースは独立して実行される

3. **Nix環境必須**
   - テスト実行にはNixがインストールされている必要がある
   - 非Nix環境での実行は想定外

## エラーハンドリング

### エラーを値として扱う
規約に従い、すべてのエラーは値として返される：

1. **プロセス実行エラー**
   ```python
   ProcessError = {
       "type": "process_error",
       "exit_code": int,
       "stderr": str,
       "timeout": bool
   }
   ```

2. **スキーマ検証エラー**
   ```python
   ValidationError = {
       "type": "validation_error",
       "schema_path": str,
       "instance_path": str,
       "message": str
   }
   ```

3. **JSON解析エラー**
   ```python
   ParseError = {
       "type": "parse_error",
       "output": str,
       "error": str
   }
   ```

フォールバック処理は行わず、エラーは明示的に報告される。

## モジュール構造

規約に従った構造：

```
contract_e2e/
├── src/
│   ├── types.py        # 型定義、データ構造
│   ├── core.py         # 純粋なテストロジック
│   ├── runner.py       # 一ファイル一関数：run_contract_tests()
│   ├── schema.py       # 一ファイル一関数：validate_schemas()
│   └── process.py      # 一ファイル一関数：execute_subprocess()
└── __init__.py         # 公開API
```

## 使用例

```bash
# E2Eテストの実行
nix run .#test.e2e

# 特定のシードでの再現
nix run .#test.e2e -- --hypothesis-seed=12345

# 詳細なレポート出力
nix run .#test.e2e -- --verbose
```