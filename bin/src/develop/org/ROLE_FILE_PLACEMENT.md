# 役割別ファイル配置と参照関係

## 最終的なファイル配置構造

```
org/                                  # 組織管理本部
├── CLAUDE.md                        # ← Definer専用設定
├── cli-definer.sh.example           # ← Definer用コマンド例
├── cli-worker.sh.example            # ← 汎用Worker管理（全員参照可）
├── application.py                   # システムAPI
├── ROLE_FILE_PLACEMENT.md          # このファイル（配置説明）
│
└── designers/                       # Designer管理
    ├── CLAUDE.md                   # ← Designer共通設定（X,Y,Z全員が参照）
    ├── cli-designer.sh.example     # ← Designer用コマンド例
    ├── x/
    │   ├── status.md               # Designer X作業記録
    │   └── instructions.md         # Designer X用指示
    ├── y/
    │   ├── status.md               # Designer Y作業記録
    │   └── instructions.md         # Designer Y用指示
    └── z/
        ├── status.md               # Designer Z作業記録
        └── instructions.md         # Designer Z用指示

※ Developer はTask Tool経由で各プロジェクトディレクトリに一時的に起動
  永続的な配置場所は持たない
```

## 各役割の参照ルール

### 1. Definer（定義者）- あなた
- **読むファイル**:
  - `org/CLAUDE.md` - メイン設定
  - `~/CLAUDE.md` - グローバル設定
- **使うコマンド**:
  - `cli-definer.sh.example`
  - `cli-worker.sh.example`
- **作成する成果物**:
  - 各プロジェクトの`REQUIREMENTS.md`

### 2. Designer X/Y/Z（設計者）
- **読むファイル**:
  - `designers/CLAUDE.md` - Designer共通設定
  - `~/CLAUDE.md` - グローバル設定
- **使うコマンド**:
  - `designers/cli-designer.sh.example`
  - `cli-worker.sh.example`
- **作成する成果物**:
  - 各プロジェクトの`SPECIFICATION.md`
  - 自分の`status.md`更新

### 3. Developer（実装者）- 新window起動
- **起動方法**:
  - Designer が `start_developer(project_dir)` で新tmux windowで起動
  - 各プロジェクトディレクトリに永続的なwindowを作成
- **管理方法**:
  - `send_command_to_developer_by_directory(dir, command)` で指示送信
  - window名: `developer:プロジェクトパス`
- **作業ディレクトリ**:
  - 実装対象のプロジェクトディレクトリ（例: `/home/nixos/bin/src/poc/email`）
- **作成する成果物**:
  - 実装コード（.py, .ts, .js等）
  - テストコード
  - 動作確認結果

## 通信フロー

```mermaid
graph TD
    A[Definer] -->|REQUIREMENTS.md| B[Designer X/Y/Z]
    B -->|SPECIFICATION.md| C[Developer]
    B -->|start_developer()新window起動| C
    B -->|send_command_to_developer_by_directory()| C
    C -->|実装結果| B
    B -->|status.md更新| A
    A -->|確認| D[ユーザー]
```

## 起動方法の違い

| 役割 | 起動方法 | 起動場所 |
|------|---------|----------|
| Definer | claude コマンド | org/ |
| Designer X/Y/Z | start_designer('x') | pane分割（同一window内） |
| Developer | start_developer(dir)（Designerから） | 新window、各プロジェクトディレクトリ |

## jsonl履歴の参照

- **Definer**: `get_claude_history('/home/nixos/bin/src/develop/org')`
- **Designer X**: `get_claude_history('/home/nixos/bin/src/develop/org/designers/x')`
- **Developer**: `get_claude_history('/各プロジェクトディレクトリ')` - 新window内で履歴管理

## 問題解決

### 以前の問題
- cli-designer.sh.exampleがorg/直下にあり、Designerが参照しづらい
- Task Tool一時起動の不安定性
- Worker概念とDeveloper概念の重複と混乱

### 解決策
- ✅ cli-designer.sh.exampleをdesigners/へ移動
- ✅ Worker → Developer概念統一と新window永続起動
- ✅ Task Tool → start_developer()関数による安定した起動
- ✅ このドキュメントで参照関係を明文化

## チェックリスト

配置確認：
- [x] Definer用ファイルはorg/直下
- [x] Designer用ファイルはdesigners/配下
- [x] Developer新window起動（application.py関数経由）
- [x] 各役割のCLAUDE.md存在確認（Definer, Designer）
- [x] cli-*.sh.example配置確認
- [x] Worker→Developer概念統一完了
- [x] 参照関係の明文化完了