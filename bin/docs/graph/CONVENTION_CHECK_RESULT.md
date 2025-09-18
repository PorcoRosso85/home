# Convention Check Result: モックの排除とVECTOR Extension調査

## 調査日時
2025-08-05

## 調査内容
1. テストファイル内のモック使用の規約適合性
2. VECTOR extension使用できない原因

## 調査結果

### 1. モックの使用について

#### 規約確認
- **本番コード内のモック**: 明確に禁止
  - `/home/nixos/bin/docs/conventions/prohibited_items.md` line 11
  - "ダミー実装・モック: 本番コード内に、テスト用のダミー実装やモックを含めること"

- **テストコード内のモック**: 明示的な禁止なし
  - `testing.md`ではインフラ層は「実際のDBや外部サービス（またはテストコンテナ）」推奨
  - ただし、E2E/統合テストの具体的実装方法には柔軟性あり

#### 現状分析
`test_incremental_indexing_spec.py`でのモック使用箇所:
- Line 25: `from unittest.mock import MagicMock, patch`
- 複数箇所でKuzuAdapterのメソッドをモック化
- 理由: VECTOR extensionが利用できない環境でもテスト可能にするため

### 2. VECTOR Extension問題

#### 実証テスト結果
```python
import vss_kuzu
result = vss_kuzu.create_vss(temp_dir)
# 結果: {'type': 'vector_extension_error', 'message': 'VECTOR extension not available', ...}
```

#### 原因
1. KuzuDBのVECTOR extensionが現在の環境に含まれていない
2. `vss_kuzu`モジュール自体は正常に動作（エラーをdictで返す）
3. nixパッケージ定義でVECTOR extensionが有効化されていない可能性

### 3. 推奨対応

#### 短期対応
- テスト内のモック使用は規約違反ではないため維持
- VECTOR extension問題は別途対応が必要

#### 中長期対応
1. **VECTOR Extension有効化**
   - `vss_kuzu-flake`のnixパッケージ定義を確認
   - KuzuDBビルド時にVECTOR extension含める設定追加
   
2. **テスト改善**
   - VECTOR extension利用可能後、実DBを使用した統合テストへ移行
   - モック使用を段階的に削減

## 結論
- **モック使用**: テストファイル内では規約違反ではない
- **VECTOR extension**: 環境構築の問題であり、別途対応が必要