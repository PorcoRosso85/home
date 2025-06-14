# 関数依存関係（FunctionDependency）の自動生成タスク

<!-- TODO -->
型の依存を定義しているFunction.schema.jsonと
機能の依存を定義するFunctionDependency.schema.jsonの
統合が必要

## 目的
- 各関数（Function型）に対応する `xxx.FunctionDependency.schema.json` ファイルを自動生成する仕組みを実装する

## 背景
現在、関数依存関係ファイルは手動で作成する必要があり、自動化の余地がある。これにより、開発効率の向上と一貫性の確保を図る。

## 具体的なタスク
1. `req-to-function` コマンドを拡張して、関数定義の生成時に同時に FunctionDependency ファイルも生成するようにする
2. 要件ファイル（`xxx.require.json`）から依存関係情報を抽出する機能を実装する
3. `function-deps` コマンドを拡張して、依存関係ファイルが存在しない場合に作成オプションを提供する

## 実装の方針
- `RequirementsToFunctionCommand` クラスを拡張して、依存関係ファイルも同時に生成する処理を追加
- 依存関係情報のモデル化と検証ロジックの実装
- スキーマ生成時のバリデーション強化

## 優先度
中 - 開発効率向上のため早期に対応することが望ましい

## 予想される難易度
中 - 既存コードの拡張が主であり、大きな構造変更は不要
