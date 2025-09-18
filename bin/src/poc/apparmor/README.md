# AppArmor POC

このディレクトリはAppArmorをNixで設定・管理するためのPOCです。

## 目的

- NixでのAppArmorプロファイル管理
- セキュリティポリシーの宣言的定義
- 開発環境でのAppArmor設定の検証

## 構成案

```
poc/apparmor/
├── README.md                 # このファイル
├── docs/                     # キャッシュしたドキュメント
│   ├── apparmor_raw1.html   # HedgeDoc記事1（生データ）
│   ├── apparmor_raw2.html   # HedgeDoc記事2（生データ）
│   ├── apparmor_nix.md      # 抽出したコンテンツ1
│   └── apparmor_guide.md    # 抽出したコンテンツ2
├── flake.nix                # Nix flake設定
├── profiles/                # AppArmorプロファイル
│   ├── example.profile      # サンプルプロファイル
│   └── development.profile  # 開発用プロファイル
└── modules/                 # Nixモジュール
    └── apparmor.nix        # AppArmor設定モジュール
```

## 議論事項

1. **プロファイル管理方法**
   - Nixモジュールとして管理するか
   - 既存のプロファイルとの統合方法

2. **開発環境での検証**
   - aa-complain/aa-enforceの切り替え
   - プロファイルのテスト方法

3. **セキュリティポリシー**
   - 最小権限の原則の実装
   - ファイルアクセス制御の設計

## 実装完了

### パイプライン構造の実現

既存のflakeをAppArmorでラップする仕組みを実装しました：

```nix
# 使用例
wrappedFlake = apparmor-wrapper.lib.wrapFlakeWithAppArmor {
  flake = original-flake;
  profileName = "restricted";
  enforceMode = false;
};
```

### テスト方法

```bash
# ラッパーのテスト
nix run -f test-wrapper.nix apps.x86_64-linux.compare

# 個別の例
nix eval .#examples.readabilityWrapped
nix eval .#examples.similarityWrapped
```

### 技術的な実現

1. **透過的なラッピング**
   - 元のflakeの構造を保持
   - 実行時にaa-execでプロファイル適用

2. **段階的適用**
   - complainモードで動作確認
   - enforceモードで本番運用

3. **互換性**
   - AppArmorが無い環境でも動作
   - 警告を出して通常実行

詳細は[USAGE.md](./USAGE.md)を参照してください。