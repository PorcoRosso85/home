# 真のパイプライン構造の設計

## 現在の問題点

現在の実装では、元のflakeに直接アクセスできてしまう：

```nix
# 迂回可能
nix run /path/to/original/flake  # AppArmorなし
nix run /path/to/wrapped/flake   # AppArmorあり
```

## 真のパイプライン構造の要件

1. **元のflakeへの直接アクセスを防ぐ**
2. **すべての実行がAppArmor経由になる**
3. **透過的で使いやすい**

## 設計案

### 案1: Overlay/Wrapper Store

```
/nix/store/original-flake → 通常のユーザーはアクセス不可
/nix/store/wrapped-flake → AppArmorでラップされたエントリポイント
```

実装方法：
- Nixのオーバーレイ機能を使用
- 元のflakeを別の場所に配置
- ラップされたバージョンのみを公開

### 案2: Nix Command Wrapper

```bash
# nixコマンド自体をラップ
alias nix='apparmor-nix'

# apparmor-nixが内部で判定
apparmor-nix run /path/to/flake
→ 自動的にAppArmorプロファイルを適用
```

### 案3: Flake Registry 制御

```nix
{
  # flakeレジストリで元のflakeを隠す
  nix.registry.original-flake = null;
  
  # ラップされたバージョンのみ登録
  nix.registry.wrapped-flake = {
    from = { type = "indirect"; id = "original-flake"; };
    to = { type = "path"; path = ./wrapped-flake; };
  };
}
```

### 案4: systemd-nspawn/bubblewrap 統合

```nix
# 実行環境全体をサンドボックス化
wrapFlakeWithSandbox = flake: {
  apps.default = {
    type = "app";
    program = pkgs.writeShellScript "sandboxed-app" ''
      exec ${pkgs.bubblewrap}/bin/bwrap \
        --ro-bind /nix/store /nix/store \
        --dev /dev \
        --proc /proc \
        --apparmor-profile ${profileName} \
        -- ${flake.apps.default.program} "$@"
    '';
  };
};
```

## 推奨アプローチ: ハイブリッド

1. **Phase 1: 現在の関数ラッパー（完了）**
   - 基本的な動作確認
   - プロファイル開発

2. **Phase 2: Nix Command Wrapper**
   - `nix run`を拡張してAppArmorを自動適用
   - フラグ `--with-apparmor` の追加

3. **Phase 3: サンドボックス統合**
   - bubblewrapとAppArmorの組み合わせ
   - 完全な隔離環境

## 実装の課題

1. **権限管理**
   - AppArmorプロファイルのロードには権限が必要
   - 一般ユーザーでの実行方法

2. **パフォーマンス**
   - ラッピングのオーバーヘッド
   - サンドボックス起動時間

3. **互換性**
   - 既存のワークフローとの統合
   - エディタやIDEとの連携

## 次のステップ

1. Nix command wrapperのプロトタイプ作成
2. bubblewrap統合のテスト
3. ユーザビリティの評価