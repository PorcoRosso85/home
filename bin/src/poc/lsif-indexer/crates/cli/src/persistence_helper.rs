//! 汎用Indexerの結果を永続化するヘルパー
use anyhow::Result;
use lsif_core::CodeGraph;
use crate::storage::IndexStorage;
use std::path::Path;

/// Indexerの結果を永続化
pub fn persist_index_result(
    graph: &CodeGraph,
    storage_path: &Path,
    key: &str
) -> Result<()> {
    let storage = IndexStorage::open(storage_path)?;
    storage.store_graph(key, graph)?;
    Ok(())
}

/// 永続化されたグラフを読み込み
pub fn load_index_result(
    storage_path: &Path,
    key: &str
) -> Result<Option<CodeGraph>> {
    let storage = IndexStorage::open(storage_path)?;
    storage.load_graph(key)
}

/// シンボル検索（永続化データから）
pub fn search_symbols(
    storage_path: &Path,
    key: &str,
    pattern: &str
) -> Result<Vec<lsif_core::Symbol>> {
    let storage = IndexStorage::open(storage_path)?;
    storage.search_symbols(key, pattern)
}
