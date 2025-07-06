# AppArmor Flake Wrapper 使用方法

## 概要

このflakeは、既存のNix flakeをAppArmorでラップするためのパイプライン機能を提供します。

```
従来: flake x (AppArmorなし)
今後: apparmor_flake(x)
```

## 基本的な使い方

### 1. 他のflakeをラップする

```nix
{
  inputs = {
    apparmor-wrapper.url = "path:/home/nixos/bin/src/poc/apparmor";
    target-flake.url = "github:some/flake";
  };

  outputs = { self, apparmor-wrapper, target-flake, ... }:
    apparmor-wrapper.lib.wrapFlakeWithAppArmor {
      flake = target-flake;
      profileName = "my-app-restricted";
      enforceMode = false;  # 開発中はcomplainモード
    };
}
```

### 2. カスタムプロファイルの使用

```nix
apparmor-wrapper.lib.wrapFlakeWithAppArmor {
  flake = target-flake;
  profileName = "custom-profile";
  profilePath = ./profiles/custom.profile;
  enforceMode = true;
}
```

## パイプライン構造の利点

1. **透過的なセキュリティ層**
   - 既存のflakeを変更せずにセキュリティを追加
   - 開発/本番環境で異なるポリシーを適用可能

2. **コンポーザブル**
   - 複数のラッパーを組み合わせ可能
   - 段階的なセキュリティ強化

3. **テスト可能**
   - complainモードで動作確認
   - enforceモードで本番運用

## 技術的な実装

### ラッピングの仕組み

1. **パッケージのラップ**
   ```nix
   original-package -> wrapped-package with aa-exec
   ```

2. **アプリのラップ**
   ```nix
   original-app -> shell script with aa-exec -> original-app
   ```

3. **プロファイルの適用**
   - aa-execを使用して実行時にプロファイルを適用
   - aa-execが利用できない場合は警告を出して通常実行

## 制限事項

1. **権限要件**
   - AppArmorプロファイルのロードには管理者権限が必要
   - 一般ユーザーでは警告が出るが実行は可能

2. **Linux限定**
   - AppArmorはLinuxカーネルの機能
   - macOS/Windowsでは無視される

3. **パフォーマンス**
   - ラッピングによる若干のオーバーヘッド
   - プロファイルチェックの処理時間

## 今後の拡張

1. **プロファイル自動生成**
   - 静的解析によるプロファイル生成
   - 学習モードでの自動収集

2. **統合テスト**
   - プロファイル違反の自動検出
   - CI/CDパイプラインへの統合

3. **プロファイルライブラリ**
   - 一般的なアプリケーション用プロファイル
   - コミュニティ共有リポジトリ