# Sync POCs - 同期システムの段階的実装

## アーキテクチャ

```
Browser ←→ [browser_sync] ←→ Server
                               ↓
                         [local_sync]     ← 基本同期エンジン
                               ↓
                        [network_sync]    ← ネットワーク障害対応
                               ↓
                      [event_sourcing]    ← イベント管理 ★
                               ↓
                        [persistence]     ← 永続化 ★
                               ↓
                    [conflict_resolution] ← 高度な競合解決 ★
```

## 実装済み ✅

### local_sync
- 単一サーバーでの同期エンジン
- ベクタークロック
- 基本的な競合解決

### network_sync  
- ネットワーク障害シミュレーション
- パケットロス、遅延、帯域幅制限
- 再接続と再送

### browser_sync
- WebSocket経由のブラウザ同期
- 共有エディタとTODOリスト

## 実装予定 ★

### event_sourcing
- イベントから状態を再構築
- スナップショット機能
- 効率的な差分計算

### persistence
- イベントログの永続化
- 高速な読み込み
- クラッシュリカバリ

### conflict_resolution
- 3-way merge
- CRDT実装
- ドメイン固有の解決

## 使用順序

1. **local_sync**: 基本を理解
2. **network_sync**: 障害への対応を学習
3. **event_sourcing**: 状態管理の基礎構築
4. **persistence**: 本番環境への対応
5. **conflict_resolution**: 高度な同期の実現