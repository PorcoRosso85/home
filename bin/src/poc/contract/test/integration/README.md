# E2E Integration Tests

## weather_dashboard_e2e.test.ts

### 責務：Contract Serviceの主要機能が正しく動作することを保証

### テスト対象機能（優先順位順）

1. **契約登録** ✅
   - Provider/Consumerの正常登録
   - 不正なスキーマの拒否

2. **自動マッチング** ✅
   - 互換性のあるサービスの発見
   - 複数Providerの管理

3. **データ変換** ✅
   - フィールド名マッピング（city ↔ location）
   - カスタム変換スクリプト（摂氏→華氏）

4. **ルーティング** ✅
   - 適切なProviderへの転送
   - 複数Provider時の選択ロジック

5. **安全な実行** ✅
   - 悪意のある変換スクリプトの隔離
   - ファイルアクセス等の権限制限

6. **エラーハンドリング** ✅
   - 不正な契約の検証
   - Provider通信エラー時のフォールバック

### テストシナリオ

複数のWeather Provider（標準版・高精度版）とDashboardの自動接続を通じて、すべての主要機能を検証。

### なぜこのテストか

- **現実的なユースケース**: 天気情報は複数ソースから取得する典型例
- **スキーマの多様性**: 同じドメインでも表現が異なる
- **選択ロジック**: コスト・精度のトレードオフ

### 実行方法

```bash
# Contract Service起動
deno task dev

# 別ターミナルでテスト実行
deno test --allow-net test/integration/weather_dashboard_e2e.test.ts
```

### テスト成功基準

すべてのステップが通過し、Contract Serviceが：
- 異なるスキーマ間の通信を仲介できる
- 悪意のあるコードから保護されている
- エラー時も適切に対応できる