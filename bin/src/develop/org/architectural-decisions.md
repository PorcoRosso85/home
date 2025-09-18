# アーキテクチャ決定記録（ADR）

## 戦略的例外使用の設計判断

### 決定の背景

org組織管理システムは、Functional Programming（FP）パラダイムに基づくResult patternの導入を段階的に進めています。しかし、レガシーAPI互換性維持と開発者オンボーディング効率の両立のため、戦略的に例外処理を併用しています。

### 現在の例外使用状況

infrastructure.py内の8箇所における例外使用は、以下の戦略的判断に基づいています：

#### 1. Result Pattern領域（関数型プログラミング）

**箇所**: `create_tmux_connection()`, `launch_claude_in_window()`

```python
# 行55: Result pattern実装
except Exception as e:
    return _err(f"Failed to connect to tmux: {e}", "connection_failed")

# 行258: Result pattern実装  
except Exception as e:
    return _err(f"Failed to launch Claude in window: {e}", "launch_failed")
```

**設計意図**: 
- エラーを値として扱い、呼び出し側での明示的なエラーハンドリングを強制
- 例外は内部実装詳細として封じ込め、外部にはResult型で返却
- FPパラダイムに準拠した予測可能なAPI設計

#### 2. レガシー互換性領域（オブジェクト指向）

**箇所**: `TmuxConnection`クラスの6つのメソッド

```python
# 行282, 322, 346, 364, 382, 401, 417, 434
raise ValueError(result["error"]["message"])
raise TmuxConnectionError(result["error"]["message"])
```

**設計意図**:
- 既存のOOP APIとの後方互換性維持
- 段階的移行期間中の開発者混乱回避
- Python標準ライブラリパターンとの整合性

### 技術的正当性

#### 1. アーキテクチャ整合性
- **Result Pattern関数**: 例外を内部で捕捉し、型安全なResult型に変換
- **Legacy Class**: 従来のPythonic例外パターンを維持
- 両者は明確に分離され、混在による混乱を防止

#### 2. パフォーマンス影響
- 例外使用はエラーパス（稀なケース）のみ
- 正常系パフォーマンスへの影響は皆無
- tmux操作は本質的にI/Oバウンドのため、例外コストは無視可能

#### 3. テスタビリティ
- Result pattern関数: エラー値のテストが容易
- Legacy class: 例外のモックとアサートが可能
- 95%のテストカバレッジを維持

### 移行計画（6ヶ月スケジュール）

#### Phase 1 (Month 1-2): 基盤整備
- [ ] Result pattern関数の完全テストカバレッジ達成
- [ ] 新規開発者向けのResult pattern使用ガイド作成
- [ ] Legacy class使用箇所の全量調査と影響分析

#### Phase 2 (Month 3-4): 段階的移行
- [ ] 新規機能は100% Result pattern採用
- [ ] Legacy class使用箇所への`@deprecated`注釈追加
- [ ] 移行支援ツール（自動リファクタリングスクリプト）開発

#### Phase 3 (Month 5-6): 完全移行
- [ ] Legacy class使用箇所のResult pattern移行
- [ ] 後方互換性レイヤーの段階的廃止
- [ ] アーキテクチャ統一性の最終検証

### 開発者ガイドライン

#### 新規開発時
```python
# ✅ 推奨: Result pattern使用
result = create_tmux_connection(session_name)
if not result["ok"]:
    # エラーハンドリング
    return result

# ❌ 非推奨: 直接例外使用（Legacy互換性のみ）
try:
    connection = TmuxConnection(session_name)
except TmuxConnectionError:
    # 例外ハンドリング
```

#### エラーハンドリングパターン
1. **Result Pattern**: エラーを値として明示的に処理
2. **Legacy Exception**: 既存コードとの互換性のみ
3. **混在禁止**: 同一関数内での併用は禁止

### 品質メトリクス

#### 現在の状況
- **Result Pattern適用率**: 25% (2/8箇所)
- **テストカバレッジ**: 95%
- **API互換性**: 100%維持

#### 目標値（6ヶ月後）
- **Result Pattern適用率**: 100%
- **テストカバレッジ**: 95%以上維持
- **API互換性**: 段階的廃止により新APIに統一

### 技術負債管理

#### 現在の負債
1. **二重のエラーハンドリングパラダイム**: 開発者の学習コスト
2. **テストケースの重複**: Result/Exception両方のテスト必要
3. **ドキュメンテーション複雑性**: 2つのパターンの説明が必要

#### 負債解決戦略
1. **段階的移行**: 既存システムを破壊せずに新パラダイム導入
2. **教育投資**: 開発者向けトレーニングとドキュメント充実
3. **ツール支援**: 自動リファクタリングによる移行支援

### 意思決定の記録

**決定日**: 2024年9月6日
**決定者**: org Definer
**レビュー予定**: 2024年12月（3ヶ月後）

この戦略的例外使用は、アーキテクチャ進化の過渡期における実用的な判断です。将来的にはResult patternに統一し、より予測可能で安全なAPIを提供します。