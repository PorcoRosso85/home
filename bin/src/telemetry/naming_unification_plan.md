# Python/TypeScript間の命名統一計画

## 原則

1. **言語固有の慣例を尊重**: snake_case (Python) vs camelCase (TypeScript)
2. **APIインターフェースの統一**: 関数シグネチャと型定義の整合性
3. **ドメイン概念の一貫性**: 同じ概念には同じ名前を使用

## 実施予定の変更

### 1. 関数シグネチャの統一

#### log関数のインターフェース統一
- **現状の問題**: TypeScriptは`LogData`型を期待、Pythonは`Dict[str, Any]`を期待
- **解決案**: 両方とも同じインターフェースに統一

**Python変更案**:
```python
# 現在
def log(level: str, data: Dict[str, Any]) -> None:
    log_data = LogData(level=level, **data)
    
# 変更後（オプション1: TypeScriptに合わせる）
def log(level: str, data: LogData) -> None:
    # dataにlevelを追加
    data_with_level = {**data, "level": level}
    
# 変更後（オプション2: 現状維持し、型定義を明確化）
def log(level: str, data: Dict[str, Any]) -> None:
    # 現在の実装を維持
```

### 2. 型定義の統一

#### LogData型の定義
- **Python**: 必須フィールドのみ定義
- **TypeScript**: 必須フィールド + 任意フィールドを明示
- **統一案**: 両方で同じ構造を明確に定義

### 3. 関数名の慣例

以下の対応関係を維持:
- Python: `to_jsonl` → TypeScript: `toJsonl`
- Python: `stdout_writer` → TypeScript: `stdoutWriter`

### 4. エクスポートパターン

- **Python**: `__all__`リストを維持
- **TypeScript**: 明示的な`export`を維持

## 実装しない変更

1. **ファイル名の変更**: 既存のインポートを壊さないため変更しない
2. **言語固有の慣例変更**: snake_case/camelCaseの変換は行わない
3. **ディレクトリ構造**: 現在の構造を維持

## 優先度

1. **高**: 関数シグネチャの統一（APIの一貫性）
2. **中**: 型定義の明確化
3. **低**: ドキュメントの統一

## 次のステップ

1. log関数のインターフェース統一方針の決定
2. テストケースの追加
3. ドキュメントの更新