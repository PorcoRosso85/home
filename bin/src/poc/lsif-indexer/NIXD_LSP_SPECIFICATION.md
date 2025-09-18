# nixd LSP接続問題修正 技術仕様書

## 問題概要
nixd LSPクライアントの作成に失敗し、Fallback Indexerで動作している状態。

## エラー詳細
```
Failed to create LSP client on attempt 1: Failed to create nix LSP client
Failed to warm up LSP client for nix: Failed to create nix LSP client
```

## 原因分析
1. **テスト環境**: nixd自体は正常起動可能
2. **実運用環境**: LSP client作成時に失敗
3. **問題箇所**: LSP通信プロトコル層

## 修正仕様

### 1. LSP Client初期化の改良
**ファイル**: `crates/lsp/src/lsp_client.rs`

#### 修正内容
- Initialize/Initialized handshakeの実装確認
- タイムアウト値の調整（3秒→5秒）
- エラーログの詳細化

### 2. NixdAdapter spawn処理の改良
**ファイル**: `crates/lsp/src/adapter/nixd.rs`

#### 修正内容
```rust
// 現在の実装
Command::new(&nixd_command).spawn()

// 修正案
let mut cmd = Command::new(&nixd_command);
cmd.stdin(Stdio::piped())
   .stdout(Stdio::piped())
   .stderr(Stdio::piped());
   
// nixd固有の環境変数設定
cmd.env("NIXD_LOG_LEVEL", "debug");
```

### 3. LSP初期化パラメータの調整
**対象**: `initialize`メソッド

#### 修正内容
- `rootUri`の適切な設定
- `workspaceFolders`の追加
- nixd固有のcapabilities設定

### 4. エラーハンドリングの強化
**全体的な改良**

#### 修正内容
- 詳細なエラーメッセージ
- リトライ機構の実装
- Fallbackへの適切な切り替え

## 実装ガイド（Developer向け）

### Step 1: デバッグログ追加
```rust
// lsp_client.rsに追加
debug!("Attempting to create nixd LSP client with command: {}", nixd_command);
debug!("NIXD_PATH environment variable: {:?}", env::var("NIXD_PATH"));
```

### Step 2: Initialize handshake改良
```rust
// 適切なinitializeパラメータ
let init_params = InitializeParams {
    root_uri: Some(Url::from_directory_path(&project_root).unwrap()),
    initialization_options: Some(json!({
        "nixd": {
            "formatting": { "command": ["nixpkgs-fmt"] }
        }
    })),
    // ... その他の設定
};
```

### Step 3: タイムアウト調整
```rust
const LSP_INIT_TIMEOUT: Duration = Duration::from_secs(5); // 3秒から5秒に
```

## 検証計画

### 1. 単体テスト
- `test_nixd_lsp_server_starts`の拡張
- Initialize handshakeの詳細テスト

### 2. 統合テスト
```bash
# nixd LSP経由でのインデックス
nix develop -c ./target/release/lsif index

# 期待結果
- "nixd LSP startup validated"メッセージ
- エラーなくNixシンボル抽出
```

### 3. デバッグ実行
```bash
RUST_LOG=trace NIXD_LOG_LEVEL=debug nix develop -c ./target/release/lsif index
```

## 成功基準
- nixd LSPクライアントが正常に作成される
- Nixファイルがnixd LSP経由でインデックスされる
- Fallbackに頼らずLSP経由で30個前後のシンボル検出

## リスクと対策
- **リスク**: nixd固有のLSP仕様への対応不足
- **対策**: nixd公式ドキュメント参照、他プロジェクトの実装例調査