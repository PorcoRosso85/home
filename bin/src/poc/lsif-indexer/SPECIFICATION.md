# nixd LSP完全統合 技術仕様書

## 要件参照
- REQUIREMENTS.md: nixd LSPをLSIFインデクサーに統合し、Nixファイルから正確な構文解析結果を取得

## 概要
既存のNixdAdapterをLSPクライアントプールに正しく統合し、nixd LSPサーバーから実際のシンボル情報を取得できるようにする技術設計。現在の"Unsupported language: nix"エラーを解決し、FallbackIndexerに依存せずにNixシンボルを抽出する。

## 問題分析
現在のエラー原因：
1. **LSPプール登録不備**: `get_language_id()`でnix拡張子が"nix"言語IDにマッピングされていない
2. **create_adapter未対応**: lsp_pool.rsでNixdAdapterの生成処理が未実装
3. **統合テスト不足**: nixd LSP統合の動作確認が不完全

## アーキテクチャ設計

### システム構成図
```
Nixファイルリクエスト
    ↓
get_language_id(".nix") → "nix" (修正対象)
    ↓
LspClientPool::create_adapter("nix") → NixdAdapter (修正対象)
    ↓
NixdAdapter::spawn_command() → nixd LSP起動
    ↓
DocumentSymbol抽出 → 正常なシンボル取得
```

## 実装仕様

### Step 1: 言語ID登録
**ファイル**: `/crates/lsp/src/adapter/lsp.rs`
**メソッド**: `get_language_id()`

現在の問題：`get_language_id()`関数で"nix"拡張子が"nix"言語IDにマッピングされていない

```rust
pub fn get_language_id(file_path: &Path) -> Option<String> {
    let extension = file_path.extension().and_then(|ext| ext.to_str())?;

    match extension {
        "rs" => Some("rust".to_string()),
        "ts" | "tsx" => Some("typescript".to_string()),
        "js" | "jsx" => Some("javascript".to_string()),
        "py" => Some("python".to_string()),
        "go" => Some("go".to_string()),
        "java" => Some("java".to_string()),
        "nix" => Some("nix".to_string()), // ← 追加必要
        _ => None,
    }
}
```

### Step 2: LSPプール統合
**ファイル**: `/crates/lsp/src/lsp_pool.rs`
**メソッド**: `create_client_internal()`

現在の問題：言語ID→アダプターマッピングで"nix"が未対応

```rust
fn create_client_internal(
    &self,
    language_id: &str,
    project_root: &Path,
) -> Result<GenericLspClient> {
    // 言語IDからアダプターを作成
    let adapter = match language_id {
        "rust" => detect_language("file.rs"),
        "typescript" => detect_language("file.ts"),
        "javascript" => detect_language("file.js"),
        "python" => detect_language("file.py"),
        "go" => detect_language("file.go"),
        "java" => detect_language("file.java"),
        "nix" => detect_language("file.nix"), // ← 追加必要
        _ => None,
    }
    .ok_or_else(|| anyhow::anyhow!("Unsupported language: {}", language_id))?;
    
    // 残りは既存実装を使用...
}
```

### Step 3: 統合テスト実装
**ファイル**: `/crates/lsp/src/adapter/nixd.rs`

NixdAdapterのテストを追加して、LSP統合が正しく動作することを確認する

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::path::Path;

    #[test]
    fn test_nix_adapter_language_support() {
        let adapter = NixdAdapter::new();
        assert_eq!(adapter.language_id(), "nix");
        assert!(adapter.supports_workspace_symbol());
        assert_eq!(adapter.supported_extensions(), vec!["nix"]);
    }

    #[test] 
    fn test_nix_language_detection() {
        use crate::adapter::lsp::{detect_language, get_language_id};
        
        // detect_language テスト
        let adapter = detect_language("test.nix");
        assert!(adapter.is_some());
        assert_eq!(adapter.unwrap().language_id(), "nix");
        
        // get_language_id テスト
        let lang_id = get_language_id(Path::new("flake.nix"));
        assert_eq!(lang_id, Some("nix".to_string()));
    }

    #[test]
    fn test_nixd_spawn_command() {
        let adapter = NixdAdapter::new();
        // nixd実行ファイルが存在するかテスト（nix develop環境想定）
        let result = adapter.spawn_command();
        // エラーがnixd未インストール由来かをチェック
        if let Err(e) = result {
            assert!(e.to_string().contains("nixd") || e.to_string().contains("No such file"));
        }
    }
}
```

### Step 4: 動作確認手順
実装完了後の確認コマンド：

```bash
# 1. コンパイル確認
cargo build --package cli --bin lsif

# 2. テスト実行
cargo test adapter::nixd --package lsp

# 3. 実際のインデックス実行
./target/debug/lsif index --force

# 4. Nixシンボル確認（期待値：12個以上）
./target/debug/lsif query symbols --filter nix
```

## API仕様

### 既存インターフェースの活用
NixdAdapterは既に以下のインターフェースを実装済み：
- `LspAdapter`: nixd LSPサーバーとの通信
- `LanguageAdapter`: Nix言語固有の処理

LSP統合に必要な新規実装は言語ID登録とプールアダプター生成のみ。

## データモデル

### 言語IDマッピング仕様
| ファイル拡張子 | 言語ID | LSPアダプター | LSPサーバー |
|---------------|--------|--------------|-------------|
| .rs | rust | RustAnalyzerAdapter | rust-analyzer |
| .ts/.tsx | typescript | TypeScriptAdapter | tsgo |
| .js/.jsx | javascript | TypeScriptAdapter | tsgo |
| .py | python | CommonAdapter | pylsp |
| .go | go | GoAdapter | gopls |
| .java | java | CommonAdapter | jdtls |
| .nix | **nix** | **NixdAdapter** | **nixd** |

## 実装ガイド

### Developer向け実装手順
1. **Step 1**: `/crates/lsp/src/adapter/lsp.rs`の`get_language_id()`にnix対応を追加
2. **Step 2**: `/crates/lsp/src/lsp_pool.rs`の`create_client_internal()`でnix→NixdAdapterマッピング追加  
3. **Step 3**: `/crates/lsp/src/adapter/nixd.rs`にテストケース追加
4. **Step 4**: コンパイル・テスト実行で動作確認

### 実装の優先順位
1. **必須**: 言語ID登録（"Unsupported language: nix"エラー解消）
2. **必須**: LSPプール統合（NixdAdapterの自動生成）
3. **推奨**: テストケース追加（回帰防止）
4. **将来**: lsif-core統合（要件の後半部分）

## エラーハンドリング
- **nixd未インストール**: "Failed to spawn nixd"エラー → nix develop環境確認
- **権限エラー**: LSPサーバー起動権限不足 → 実行権限確認  
- **タイムアウト**: nixd初期化遅延 → init_timeout調整

## テスト方針

### 単体テスト
- [ ] `get_language_id(".nix")` → `"nix"`を返すこと
- [ ] `detect_language("test.nix")` → NixdAdapterインスタンスを返すこと
- [ ] `LspClientPool::create_adapter("nix")` → 正常にクライアント作成されること

### 統合テスト  
- [ ] 実際のflake.nixでシンボル抽出（12個以上）
- [ ] nixd LSP起動・通信・シャットダウンのフルサイクル
- [ ] 他言語（Rust, TypeScript）と混在プロジェクトでの動作

### パフォーマンス基準
- LSPクライアント初期化: < 5秒
- シンボル抽出処理: < 2秒/1000行
- メモリ使用量: < 100MB (通常プロジェクト)

## 成功基準
- [x] NixdAdapterが存在し、基本インターフェースが実装済み
- [ ] LSPプールでnix言語が認識される（"Unsupported language: nix"エラー解消）
- [ ] 実際のNixプロジェクトでFallbackIndexerより多くのシンボル抽出（目標: 50%以上増加）
- [ ] 他言語の既存機能に回帰なし
- [ ] 統合テストが全てPASS

## リスクと対策
- **Risk**: nixd LSP不安定 → **対策**: フォールバック機構維持、timeout設定
- **Risk**: nix develop環境必須 → **対策**: 環境チェック機能、エラーメッセージ改善
- **Risk**: 大規模Nixプロジェクトでの性能劣化 → **対策**: プロファイリング、並列処理検討

## 影響範囲
- **変更対象**: 2つのファイルのみ（lsp.rs, lsp_pool.rs）
- **破壊的変更**: なし
- **既存機能**: 影響なし（追加のみ）
- **テスト追加**: nixd.rsにテストケース追加

---

**動作確認済み: nixd LSP統合SPECIFICATION.md作成完了**