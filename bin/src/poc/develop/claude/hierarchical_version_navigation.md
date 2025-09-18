# 階層的バージョン状態ナビゲーション

## 重要な前提
- **作業ディレクトリには必ずflake.nixが存在**
- **ディレクトリパスから現在位置が完全に把握可能**
- **GraphDBにはディレクトリ毎のバージョン状態が定義済み**

## 階層構造とバージョン管理

```
[GraphDB内の状態定義]

/projects/web_api/ (version: 2.0)
    │
    ├─ 期待状態: "RESTful API完成"
    ├─ 必要モジュール: ["auth", "db", "api"]
    │
    ├─ /projects/web_api/src/ (version: 2.0)
    │   ├─ 期待状態: "全モジュール統合"
    │   │
    │   ├─ /projects/web_api/src/auth/ (version: 1.3)
    │   │   ├─ 期待状態: "JWT認証実装完了"
    │   │   ├─ 必要ファイル: ["jwt.rs", "middleware.rs", "tests.rs"]
    │   │   └─ 次バージョン: 1.4 (OAuth追加)
    │   │
    │   └─ /projects/web_api/src/db/ (version: 0.9)
    │       ├─ 期待状態: "接続プール実装"
    │       └─ 次バージョン: 1.0 (マイグレーション追加)
    │
    └─ flake.nix (Rust環境定義)
```

## memberの位置認識フロー

### 1. 自分の位置を確認

```
[Claude member]
    │
    ├─ pwd: /home/nixos/.worktrees/claude-org/auth-impl-123456/
    ├─ 実際の作業: src/auth/
    └─ flake.nix確認: Rustプロジェクト
```

### 2. GraphDBに現在位置の状態を問い合わせ

```cypher
// 現在のディレクトリの期待状態を取得
MATCH (d:Directory {path: '/projects/web_api/src/auth/'})
RETURN d.version, d.expected_state, d.required_files

// 結果
{
  "version": "1.3",
  "expected_state": "JWT認証実装完了",
  "required_files": ["jwt.rs", "middleware.rs", "tests.rs"]
}
```

### 3. 親ディレクトリの文脈も確認（再帰的）

```cypher
// 親ディレクトリを辿って全体像を把握
MATCH path = (child:Directory {path: '/projects/web_api/src/auth/'})
  -[:CHILD_OF*]->(parent:Directory)
RETURN path

// 取得できる情報
Level 0 (you): /projects/web_api/ → "次バージョン2.0はREST API完成"
Level 1: /projects/web_api/src/ → "認証・DB・API統合"
Level 2 (me): /projects/web_api/src/auth/ → "JWT実装"
```

## 実装例：memberの自律的な状態把握

```
[Claude member の動作]
    │
    ├─ 「私は src/auth/ にいます」
    │
    ├─ GraphDB照会
    │   「このディレクトリの期待状態は？」
    │   → "JWT認証実装完了 (v1.3)"
    │
    ├─ 現状確認
    │   「必要ファイルは揃っているか？」
    │   ├─ jwt.rs ✅
    │   ├─ middleware.rs ❌
    │   └─ tests.rs ❌
    │
    └─ 実装計画
        「middleware.rsとtests.rsを作成して
         バージョン1.3の完成を目指します」
```

## 階層的な意思決定

### 上位の要求を理解

```
[GraphDB クエリ結果の解釈]
    │
    ├─ Level 0: "プロジェクト全体でREST API必要"
    ├─ Level 1: "srcディレクトリで統合必要"
    └─ Level 2: "私の担当はJWT認証部分"
            │
            └─ 「なるほど、私の作業は全体のREST APIの
                認証部分を担当しているのか」
```

### 次バージョンへの準備

```
現在: v1.3 (JWT基本実装)
    │
    ├─ GraphDB: "次はv1.4でOAuth追加予定"
    │
    └─ member: 「現在の実装をOAuth拡張可能な
                設計にしておこう」
```

## この設計の利点

1. **完全な文脈把握**: 自分の作業が全体のどこに位置するか明確
2. **自律的な判断**: 期待状態に向けて何をすべきか自己決定
3. **将来を見据えた実装**: 次バージョンを考慮した設計
4. **品質基準の明確化**: 各バージョンの完了条件が明確

## 実装への影響

```bash
# memberは以下の情報で自律的に動作可能
- 現在地: pwd + flake.nix
- 期待状態: GraphDBから取得
- 実装内容: 期待状態と現状の差分
- 品質基準: GraphDBのversion定義
```

これにより、spec_idなしでも、memberは十分な情報を持って作業できます。