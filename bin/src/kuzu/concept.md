# KuzuDB: Decision Management as Version Control

## Core Insight: VersionState = Decision Log

KuzuDBにおけるVersionStateは、単なるバージョン管理ではなく、**決定（Decision）の積み重ねログ**として機能します。

```
v2.0.0: 「認証機能を作る」という決定
  ↓
v2.0.1: 「JWTが必要だった」という追加決定  
  ↓
v2.1.0: 「決済も必要」という新たな決定
  ↓
v3.0.0: 「requirement_typeを細分化する」という設計決定
```

## イミュータブルな決定履歴

過去の決定は変更せず、新バージョンで状態を更新：

```cypher
// 過去の決定は変更せず、新バージョンで上書き
v2.0.0: CREATE (auth:RequirementEntity {requirement_type: "feature"})
v3.0.0: MATCH (auth) SET auth.requirement_type = "feature:authentication"
```

これは**Gitと同じ哲学**：
- 過去のコミット（決定）は変更しない
- 新しいコミット（VersionState）で状態を更新
- 全ての決定の経緯が追跡可能

## KuzuDB-LLM-人間のフィードバックループ

```
1. KuzuDB: 「v2.1.0で決済機能追加されたけど、依存関係が未解決」
     ↓
2. LLM: 「過去の決定を分析すると、トランザクションログが必要では？」
     ↓
3. 人間: 「その通り。v3.0.0で追加しよう」
     ↓
4. 新Version作成 → 決定を記録
```

## 実装の含意

1. **Decisionテーブル不要**: VersionState自体が決定ログ
2. **変更は新Version**: 過去を書き換えず、新しい層を追加
3. **完全な監査証跡**: いつ、なぜ、何を決定したか全て残る

現在のDDLは**すでに決定管理システム**として機能しており、追加で必要なのは：
- `CONFLICTS_WITH`関係（矛盾検出用）
- 運用ルール（requirement_typeの使い方など）

## 哲学的な整理

**「Git manages the past, KuzuDB manages the future」**
→ より正確には
**「Both manage decisions - Git for code, KuzuDB for plans」**

Gitがコードの決定履歴を管理するように、KuzuDBは計画の決定履歴を管理する。
両者は相補的な関係にあり、ソフトウェア開発の全ライフサイクルをカバーする。