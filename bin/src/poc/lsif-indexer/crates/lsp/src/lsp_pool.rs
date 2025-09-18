use anyhow::{Context, Result};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::{
    atomic::{AtomicUsize, Ordering},
    Arc, Mutex,
};
use std::time::{Duration, Instant};
use tracing::{debug, info, warn};

use crate::adapter::lsp::{detect_language, get_language_id, GenericLspClient};

type LanguageId = String;

/// LSPクライアントプール - LSPサーバーの再利用と管理
pub struct LspClientPool {
    /// 言語IDごとのクライアントプール（複数インスタンス対応）
    clients: Arc<Mutex<HashMap<LanguageId, Vec<PooledClient>>>>,
    /// プールの設定
    config: PoolConfig,
    /// 次のインスタンスID
    next_instance_id: Arc<AtomicUsize>,
}

/// プールされたクライアント
struct PooledClient {
    /// 実際のLSPクライアント
    client: Arc<Mutex<GenericLspClient>>,
    /// 最後に使用された時刻
    last_used: Instant,
    /// プロジェクトルート
    project_root: PathBuf,
    /// 参照カウント
    ref_count: usize,
    /// サポートするCapabilitiesのサマリー
    capabilities_summary: CapabilitiesSummary,
    /// インスタンスID
    instance_id: usize,
}

/// Capabilitiesのサマリー（高速アクセス用）
#[derive(Clone, Debug)]
struct CapabilitiesSummary {
    /// ドキュメントシンボルのサポート
    pub supports_document_symbol: bool,
    /// 定義へのジャンプのサポート
    pub supports_definition: bool,
    /// 参照検索のサポート
    pub supports_references: bool,
    /// 型定義へのジャンプのサポート
    pub supports_type_definition: bool,
    /// 実装へのジャンプのサポート
    pub supports_implementation: bool,
    /// ワークスペースシンボル検索のサポート
    pub supports_workspace_symbol: bool,
    /// コール階層のサポート
    pub supports_call_hierarchy: bool,
    /// セマンティックトークンのサポート
    pub supports_semantic_tokens: bool,
}

/// プール設定
#[derive(Clone, Debug)]
pub struct PoolConfig {
    /// 言語ごとの最大インスタンス数（推奨: 4）
    pub max_instances_per_language: usize,
    /// クライアントの最大アイドル時間
    pub max_idle_time: Duration,
    /// 初期化タイムアウト（適応的に変更される）
    pub init_timeout: Duration,
    /// リクエストタイムアウト（適応的に変更される）
    pub request_timeout: Duration,
    /// 最大リトライ回数
    pub max_retries: usize,
}

impl Default for PoolConfig {
    fn default() -> Self {
        Self {
            max_instances_per_language: 4, // パフォーマンス分析に基づく推奨値
            max_idle_time: Duration::from_secs(300), // 5分
            init_timeout: Duration::from_secs(8), // 初回: 8秒 (increased for nixd)
            request_timeout: Duration::from_secs(2), // 通常: 2秒
            max_retries: 1,                // リトライ1回のみ（高速化）
        }
    }
}

impl LspClientPool {
    /// 新しいプールを作成
    pub fn new(config: PoolConfig) -> Self {
        Self {
            clients: Arc::new(Mutex::new(HashMap::new())),
            config,
            next_instance_id: Arc::new(AtomicUsize::new(0)),
        }
    }

    /// デフォルト設定でプールを作成
    pub fn with_defaults() -> Self {
        Self::new(PoolConfig::default())
    }

    /// 言語のCapabilities情報を取得
    pub fn get_capabilities_for_language(&self, language_id: &str) -> Option<CapabilitiesSummary> {
        let clients = self.clients.lock().unwrap();
        clients
            .get(language_id)
            .and_then(|instances| instances.first())
            .map(|pooled| pooled.capabilities_summary.clone())
    }

    /// Capabilityがサポートされているかチェック（プールされたクライアントから）
    pub fn has_capability_for_language(&self, language_id: &str, capability: &str) -> bool {
        let clients = self.clients.lock().unwrap();
        if let Some(instances) = clients.get(language_id) {
            if let Some(pooled) = instances.first() {
                match capability {
                    "textDocument/documentSymbol" => {
                        pooled.capabilities_summary.supports_document_symbol
                    }
                    "textDocument/definition" => pooled.capabilities_summary.supports_definition,
                    "textDocument/references" => pooled.capabilities_summary.supports_references,
                    "textDocument/typeDefinition" => {
                        pooled.capabilities_summary.supports_type_definition
                    }
                    "textDocument/implementation" => {
                        pooled.capabilities_summary.supports_implementation
                    }
                    "workspace/symbol" => pooled.capabilities_summary.supports_workspace_symbol,
                    "textDocument/prepareCallHierarchy" => {
                        pooled.capabilities_summary.supports_call_hierarchy
                    }
                    "textDocument/semanticTokens" => {
                        pooled.capabilities_summary.supports_semantic_tokens
                    }
                    _ => false,
                }
            } else {
                false
            }
        } else {
            false
        }
    }

    /// クライアントを取得または作成
    pub fn get_or_create_client(
        &self,
        file_path: &Path,
        project_root: &Path,
    ) -> Result<Arc<Mutex<GenericLspClient>>> {
        // 言語を検出
        let language_id = get_language_id(file_path)
            .ok_or_else(|| anyhow::anyhow!("Unsupported file type: {}", file_path.display()))?;

        // 既存のクライアントをチェック（ラウンドロビン方式で負荷分散）
        {
            let mut clients = self.clients.lock().unwrap();

            if let Some(instances) = clients.get_mut(&language_id) {
                // 同じプロジェクトルートで最も使用されていないインスタンスを選択
                let mut best_instance = None;
                let mut min_ref_count = usize::MAX;

                for (idx, pooled) in instances.iter_mut().enumerate() {
                    if pooled.project_root == project_root && pooled.ref_count < min_ref_count {
                        min_ref_count = pooled.ref_count;
                        best_instance = Some(idx);
                    }
                }

                if let Some(idx) = best_instance {
                    let pooled = &mut instances[idx];
                    pooled.last_used = Instant::now();
                    pooled.ref_count += 1;
                    debug!(
                        "Reusing LSP client for {} (instance: {}, ref_count: {})",
                        language_id, pooled.instance_id, pooled.ref_count
                    );
                    return Ok(Arc::clone(&pooled.client));
                }
            }
        }

        // 新しいクライアントを作成（インスタンス数制限をチェック）
        {
            let mut clients = self.clients.lock().unwrap();
            let instances = clients.entry(language_id.clone()).or_default();

            // 最大インスタンス数を超えている場合は最も古いアイドルインスタンスを削除
            if instances.len() >= self.config.max_instances_per_language {
                // ref_countが0で最も古いインスタンスを探す
                let mut oldest_idle_idx = None;
                let mut oldest_time = Instant::now();

                for (idx, pooled) in instances.iter().enumerate() {
                    if pooled.ref_count == 0 && pooled.last_used < oldest_time {
                        oldest_time = pooled.last_used;
                        oldest_idle_idx = Some(idx);
                    }
                }

                if let Some(idx) = oldest_idle_idx {
                    info!(
                        "Removing idle LSP instance for {} (instance: {})",
                        language_id, instances[idx].instance_id
                    );
                    instances.remove(idx);
                } else {
                    warn!(
                        "All {} instances for {} are in use, cannot create new instance",
                        self.config.max_instances_per_language, language_id
                    );
                    // 最初のインスタンスを返す（負荷分散のため）
                    if let Some(pooled) = instances.first_mut() {
                        pooled.ref_count += 1;
                        return Ok(Arc::clone(&pooled.client));
                    }
                }
            }
        }

        info!("Creating new LSP client for {}", language_id);
        let new_client = self.create_client_with_retry(&language_id, project_root)?;

        // Capabilitiesのサマリーを作成
        let capabilities_summary = CapabilitiesSummary {
            supports_document_symbol: new_client.has_capability("textDocument/documentSymbol"),
            supports_definition: new_client.has_capability("textDocument/definition"),
            supports_references: new_client.has_capability("textDocument/references"),
            supports_type_definition: new_client.has_capability("textDocument/typeDefinition"),
            supports_implementation: new_client.has_capability("textDocument/implementation"),
            supports_workspace_symbol: new_client.has_capability("workspace/symbol"),
            supports_call_hierarchy: new_client.has_capability("textDocument/prepareCallHierarchy"),
            supports_semantic_tokens: new_client.has_capability("textDocument/semanticTokens"),
        };

        debug!(
            "LSP client capabilities for {}: {:?}",
            language_id, capabilities_summary
        );

        // プールに追加
        let client_arc = Arc::new(Mutex::new(new_client));
        {
            let mut clients = self.clients.lock().unwrap();
            let instances = clients.entry(language_id.clone()).or_default();
            let instance_id = instances.len();

            instances.push(PooledClient {
                client: Arc::clone(&client_arc),
                last_used: Instant::now(),
                project_root: project_root.to_path_buf(),
                ref_count: 1,
                capabilities_summary,
                instance_id,
            });

            info!(
                "Created LSP instance {} for {} (total instances: {})",
                instance_id,
                language_id,
                instances.len()
            );
        }

        // 作成したクライアントを返す
        Ok(client_arc)
    }

    /// リトライ付きでクライアントを作成
    fn create_client_with_retry(
        &self,
        language_id: &str,
        project_root: &Path,
    ) -> Result<GenericLspClient> {
        let mut last_error = None;

        for attempt in 1..=self.config.max_retries {
            debug!(
                "Attempting to create LSP client (attempt {}/{})",
                attempt, self.config.max_retries
            );

            match self.create_client_internal(language_id, project_root) {
                Ok(client) => {
                    info!("Successfully created LSP client on attempt {}", attempt);
                    return Ok(client);
                }
                Err(e) => {
                    warn!("Failed to create LSP client on attempt {}: {}", attempt, e);
                    last_error = Some(e);

                    if attempt < self.config.max_retries {
                        // さらに短縮された指数バックオフ（5ms, 10ms, 20ms...）
                        std::thread::sleep(Duration::from_millis(5 * (2_u64.pow(attempt as u32))));
                        // 50ms -> 5ms
                    }
                }
            }
        }

        Err(last_error.unwrap_or_else(|| anyhow::anyhow!("Failed to create LSP client")))
    }

    /// 実際のクライアント作成処理
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
            "nix" => detect_language("file.nix"),
            _ => None,
        }
        .ok_or_else(|| anyhow::anyhow!("Unsupported language: {}", language_id))?;

        // LSPサーバーを起動（初期化なし）
        let mut client = GenericLspClient::new_uninit(adapter)
            .with_context(|| format!("Failed to create {} LSP client", language_id))?;

        // プロジェクトルートを指定して初期化
        let init_start = Instant::now();
        client
            .initialize(project_root, Some(self.config.init_timeout))
            .with_context(|| format!("Failed to initialize {} LSP client", language_id))?;

        let init_duration = init_start.elapsed();
        info!(
            "LSP client for {} initialized in {:?}",
            language_id, init_duration
        );

        Ok(client)
    }

    /// クライアントを解放
    pub fn release_client(&self, language_id: &str) {
        let mut clients = self.clients.lock().unwrap();

        if let Some(instances) = clients.get_mut(language_id) {
            // 最初のref_count > 0のインスタンスを探す
            for pooled in instances.iter_mut() {
                if pooled.ref_count > 0 {
                    pooled.ref_count -= 1;
                    debug!(
                        "Released LSP client for {} (instance: {}, ref_count: {})",
                        language_id, pooled.instance_id, pooled.ref_count
                    );
                    break;
                }
            }
        }
    }

    /// アイドルクライアントをクリーンアップ
    pub fn cleanup_idle_clients(&self) {
        let mut clients = self.clients.lock().unwrap();
        let now = Instant::now();

        for (language_id, instances) in clients.iter_mut() {
            instances.retain(|pooled| {
                let idle_time = now - pooled.last_used;
                let should_keep = pooled.ref_count > 0 || idle_time < self.config.max_idle_time;

                if !should_keep {
                    info!(
                        "Cleaning up idle LSP instance for {} (instance: {})",
                        language_id, pooled.instance_id
                    );
                }

                should_keep
            });
        }

        // 空になった言語エントリを削除
        clients.retain(|_, instances| !instances.is_empty());
    }

    /// すべてのクライアントをシャットダウン
    pub fn shutdown_all(&self) {
        let mut clients = self.clients.lock().unwrap();

        for language_id in clients.keys().cloned().collect::<Vec<_>>() {
            info!("Shutting down LSP client for {}", language_id);
        }

        // クライアントをクリア（デストラクタがシャットダウンを処理）
        clients.clear();
    }

    /// 統計情報を取得
    pub fn get_stats(&self) -> PoolStats {
        let clients = self.clients.lock().unwrap();

        let mut total = 0;
        let mut active = 0;

        for instances in clients.values() {
            total += instances.len();
            active += instances.iter().filter(|p| p.ref_count > 0).count();
        }

        PoolStats {
            total_clients: total,
            active_clients: active,
            languages: clients.keys().cloned().collect(),
        }
    }

    /// プロジェクト内の全言語のLSPクライアントを事前起動（ウォームアップ）
    pub fn warm_up(&self, project_root: &Path, languages: &[&str]) -> Result<()> {
        if languages.is_empty() {
            info!("No languages to warm up, skipping LSP initialization");
            return Ok(());
        }

        info!("🚀 Starting LSP warm-up for {} language(s): {:?}", languages.len(), languages);
        let start = Instant::now();

        let mut successful_starts = Vec::new();
        let mut failed_starts = Vec::new();

        for language_id in languages {
            info!("🔧 Initializing LSP server for {}", language_id);
            match self.get_or_create_client_for_language(language_id, project_root) {
                Ok(_) => {
                    info!("✅ Successfully warmed up LSP client for {}", language_id);
                    successful_starts.push(*language_id);
                }
                Err(e) => {
                    // エラーは警告として記録するが、処理は続行
                    warn!("❌ Failed to warm up LSP client for {}: {}", language_id, e);
                    failed_starts.push(*language_id);
                }
            }
        }

        let duration = start.elapsed();
        
        // サマリー情報を出力
        if !successful_starts.is_empty() {
            info!(
                "🎉 LSP warm-up completed in {:.2}s - Successfully started {} LSP server(s): {:?}",
                duration.as_secs_f64(),
                successful_starts.len(),
                successful_starts
            );
        }
        
        if !failed_starts.is_empty() {
            warn!(
                "⚠️  Failed to start {} LSP server(s): {:?}",
                failed_starts.len(),
                failed_starts
            );
        }

        // 環境変数設定のヒントを出力
        if std::env::var("LSIF_ENABLED_LANGUAGES").is_ok() {
            info!("📝 Note: LSP language selection is controlled by LSIF_ENABLED_LANGUAGES environment variable");
        }

        Ok(())
    }

    /// 特定言語のクライアントを取得または作成（ファイルパスなし）
    pub fn get_or_create_client_for_language(
        &self,
        language_id: &str,
        project_root: &Path,
    ) -> Result<Arc<Mutex<GenericLspClient>>> {
        // 既存のクライアントをチェック
        {
            let mut clients = self.clients.lock().unwrap();

            if let Some(pooled_vec) = clients.get_mut(language_id) {
                // プロジェクトルートが同じクライアントを探す
                for pooled in pooled_vec.iter_mut() {
                    if pooled.project_root == project_root {
                        pooled.last_used = Instant::now();
                        pooled.ref_count += 1;
                        debug!(
                            "Reusing LSP client for {} (ref_count: {})",
                            language_id, pooled.ref_count
                        );
                        return Ok(Arc::clone(&pooled.client));
                    }
                }
            }
        }

        // 新しいクライアントを作成
        info!("Creating new LSP client for {}", language_id);
        let new_client = self.create_client_with_retry(language_id, project_root)?;

        // Capabilitiesのサマリーを作成
        let capabilities_summary = CapabilitiesSummary {
            supports_document_symbol: new_client.has_capability("textDocument/documentSymbol"),
            supports_definition: new_client.has_capability("textDocument/definition"),
            supports_references: new_client.has_capability("textDocument/references"),
            supports_type_definition: new_client.has_capability("textDocument/typeDefinition"),
            supports_implementation: new_client.has_capability("textDocument/implementation"),
            supports_workspace_symbol: new_client.has_capability("workspace/symbol"),
            supports_call_hierarchy: new_client.has_capability("textDocument/prepareCallHierarchy"),
            supports_semantic_tokens: new_client.has_capability("textDocument/semanticTokens"),
        };

        debug!(
            "LSP client capabilities for {}: {:?}",
            language_id, capabilities_summary
        );

        // プールに追加
        let client_arc = Arc::new(Mutex::new(new_client));
        {
            let mut clients = self.clients.lock().unwrap();
            let instance_id = self.next_instance_id.fetch_add(1, Ordering::SeqCst);

            let pooled_client = PooledClient {
                client: Arc::clone(&client_arc),
                last_used: Instant::now(),
                project_root: project_root.to_path_buf(),
                ref_count: 1,
                capabilities_summary,
                instance_id,
            };

            // Vec<PooledClient>を取得または作成
            clients
                .entry(language_id.to_string())
                .or_default()
                .push(pooled_client);
        }

        // 作成したクライアントを返す
        Ok(client_arc)
    }
}

/// プール統計情報
#[derive(Debug)]
pub struct PoolStats {
    pub total_clients: usize,
    pub active_clients: usize,
    pub languages: Vec<String>,
}

/// スコープ付きクライアント（自動解放）
pub struct ScopedClient<'a> {
    pool: &'a LspClientPool,
    language_id: String,
    client: Arc<Mutex<GenericLspClient>>,
}

impl<'a> ScopedClient<'a> {
    pub fn new(pool: &'a LspClientPool, file_path: &Path, project_root: &Path) -> Result<Self> {
        let language_id =
            get_language_id(file_path).ok_or_else(|| anyhow::anyhow!("Unsupported file type"))?;
        let client = pool.get_or_create_client(file_path, project_root)?;

        Ok(Self {
            pool,
            language_id,
            client,
        })
    }

    pub fn client(&self) -> &Arc<Mutex<GenericLspClient>> {
        &self.client
    }
}

impl<'a> Drop for ScopedClient<'a> {
    fn drop(&mut self) {
        self.pool.release_client(&self.language_id);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    #[test]
    fn test_pool_creation() {
        let pool = LspClientPool::with_defaults();
        let stats = pool.get_stats();
        assert_eq!(stats.total_clients, 0);
        assert_eq!(stats.active_clients, 0);
    }

    #[test]
    fn test_pool_config() {
        let config = PoolConfig {
            max_instances_per_language: 4,
            max_idle_time: Duration::from_secs(60),
            init_timeout: Duration::from_secs(10),
            request_timeout: Duration::from_secs(2),
            max_retries: 5,
        };

        let pool = LspClientPool::new(config.clone());
        assert_eq!(pool.config.max_retries, 5);
        assert_eq!(pool.config.init_timeout, Duration::from_secs(10));
    }

    #[test]
    fn test_scoped_client() {
        let temp_dir = TempDir::new().unwrap();
        let test_file = temp_dir.path().join("test.rs");
        fs::write(&test_file, "fn main() {}").unwrap();

        let pool = LspClientPool::with_defaults();

        {
            // ScopedClientのスコープ
            let _client = ScopedClient::new(&pool, &test_file, temp_dir.path());
            let stats = pool.get_stats();
            // 注: 実際のLSPサーバーが起動できない環境では0になる
            assert!(stats.total_clients <= 1);
        }

        // スコープ外でref_countが減る
        pool.cleanup_idle_clients();
    }
}
