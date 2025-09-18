# TDD Red Phase - 03_single_container_1000_clients

## 概要

このフェーズでは、単一コンテナの限界を実証する**失敗するテスト**を作成しました。

## 失敗する理由

1. **1000同時接続は単一コンテナの限界を超える**
   - 02の実装（100クライアント）の10倍の負荷
   - システムリソースの枯渇が予想される

2. **期待される失敗パターン**
   - 500-750クライアントで破綻点に到達
   - P99レイテンシが100msを大幅に超過
   - エラー率が急激に上昇
   - メモリ使用量が1GBを超過

## テストの実行方法

```bash
# 02のサーバーを起動（03はまだ実装していない）
cd ../02_single_container_100_clients
deno task start

# 別ターミナルで03のテストを実行
cd ../03_single_container_1000_clients
deno task test:red
```

## 期待される結果

```
❌ Expected to handle 1000+ connections, but only handled 500-750
❌ System broke at 750 clients - single container cannot handle 1000 clients
❌ P99 latency 500ms exceeds 100ms limit with 1000 clients
❌ Error rate 25.00% exceeds 1% limit
❌ Memory usage 1500.00MB exceeds 1GB limit
❌ Memory growth rate 150.00% indicates resource exhaustion
```

## 次のステップ

これらの失敗を受けて、Green Phaseでは：
1. 低レベルTCP最適化
2. メモリプール実装
3. ゼロコピー操作
4. カーネルパラメータチューニング

しかし、これらの最適化でも**単一コンテナの物理的限界**は超えられないことを実証します。